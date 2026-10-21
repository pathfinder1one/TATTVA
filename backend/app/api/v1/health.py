"""Process liveness and dependency readiness endpoints."""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from app.config import Settings, get_settings
from app.repositories.indexes import ensure_indexes
from app.services.qdrant_store import ensure_collection

router = APIRouter(tags=["health"])


@router.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/readyz")
async def readyz(request: Request, settings: Settings = Depends(get_settings)):
    if not request.app.state.indexes_ready:
        try:
            await ensure_indexes(request.app.state.database)
            request.app.state.indexes_ready = True
        except Exception:
            pass
    try:
        await request.app.state.database.command("ping")
    except Exception:
        return JSONResponse(status_code=503, content={
            "status": "not_ready",
            "dependencies": {"mongodb": "unavailable", "indexes": "unknown"},
        })
    if not request.app.state.indexes_ready:
        return JSONResponse(status_code=503, content={
            "status": "not_ready",
            "dependencies": {"mongodb": "ok", "indexes": "unavailable", "qdrant": "unknown"},
        })
    try:
        if not request.app.state.qdrant_ready:
            await ensure_collection(request.app.state.qdrant, settings)
            request.app.state.qdrant_ready = True
        else:
            await request.app.state.qdrant.get_collections()
    except Exception:
        return JSONResponse(status_code=503, content={
            "status": "not_ready",
            "dependencies": {"mongodb": "ok", "indexes": "ready", "qdrant": "unavailable"},
        })
    return {"status": "ready", "dependencies": {"mongodb": "ok", "indexes": "ready", "qdrant": "ok"}}
