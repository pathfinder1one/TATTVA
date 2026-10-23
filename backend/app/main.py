import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pymongo import AsyncMongoClient
from qdrant_client import AsyncQdrantClient

from app.api.v1.router import api_router
from app.api.v1.health import router as health_router
from app.config import get_settings
from app.core.errors import install_exception_handlers
from app.core.logging import configure_logging
from app.core.correlation import RequestCorrelationMiddleware
from app.repositories.indexes import ensure_indexes
from app.services.qdrant_store import ensure_collection
from app.workers.run_analysis import analysis_worker_loop

settings = get_settings()
configure_logging(settings.log_level)


@asynccontextmanager
async def lifespan(app: FastAPI):
    mongo = AsyncMongoClient(settings.mongodb_uri, serverSelectionTimeoutMS=3000)
    qdrant = AsyncQdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key or None)
    app.state.mongo = mongo
    app.state.database = mongo[settings.mongodb_database]
    app.state.indexes_ready = False
    app.state.qdrant = qdrant
    app.state.qdrant_ready = False
    app.state.voice_semaphore = asyncio.Semaphore(settings.voice_max_concurrent_sessions)
    Path(settings.file_storage_root).mkdir(parents=True, exist_ok=True)
    Path(settings.embedding_cache_root).mkdir(parents=True, exist_ok=True)
    try:
        await ensure_indexes(app.state.database)
        app.state.indexes_ready = True
    except Exception:
        # Keep /healthz available while /readyz reports dependency failure.
        pass
    try:
        await ensure_collection(qdrant, settings)
        app.state.qdrant_ready = True
    except Exception:
        pass
    worker_tasks = []
    if settings.run_analysis_workers:
        worker_tasks = [
            asyncio.create_task(analysis_worker_loop(app.state.database, qdrant, settings))
            for _ in range(settings.max_concurrent_runs)
        ]
    app.state.analysis_workers = worker_tasks
    yield
    for worker in worker_tasks:
        worker.cancel()
    await asyncio.gather(*worker_tasks, return_exceptions=True)
    await mongo.close()
    await qdrant.close()


app = FastAPI(
    title="TATTVA Backend API",
    version="0.1.0",
    description="Evidence-first, case-scoped analysis backend foundation.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins if settings.app_env != "development" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestCorrelationMiddleware)
install_exception_handlers(app)
app.include_router(api_router, prefix="/api/v1")
app.include_router(health_router)


@app.get("/", include_in_schema=False)
async def root() -> dict[str, str]:
    return {"service": "tattva-backend", "docs": "/docs"}


