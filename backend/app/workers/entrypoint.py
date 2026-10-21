"""Dedicated process entry point for Mongo-backed analysis workers."""

import asyncio
import logging

from pymongo import AsyncMongoClient
from qdrant_client import AsyncQdrantClient

from app.config import get_settings
from app.core.logging import configure_logging
from app.repositories.indexes import ensure_indexes
from app.services.qdrant_store import ensure_collection
from app.workers.run_analysis import analysis_worker_loop

logger = logging.getLogger(__name__)


async def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    mongo = AsyncMongoClient(settings.mongodb_uri, serverSelectionTimeoutMS=3000)
    qdrant = AsyncQdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key or None)
    database = mongo[settings.mongodb_database]
    try:
        await ensure_indexes(database)
        await ensure_collection(qdrant, settings)
        logger.info("Analysis worker process started concurrency=%s", settings.max_concurrent_runs)
        await asyncio.gather(*(
            analysis_worker_loop(database, qdrant, settings)
            for _ in range(settings.max_concurrent_runs)
        ))
    finally:
        await mongo.close()
        await qdrant.close()


if __name__ == "__main__":
    asyncio.run(main())
