import asyncio
import threading
from functools import lru_cache
from pathlib import Path

from app.config import Settings

_model_lock = threading.Lock()


@lru_cache(maxsize=4)
def _load_model(model_name: str, cache_root: str):
    from fastembed import TextEmbedding

    Path(cache_root).mkdir(parents=True, exist_ok=True)
    return TextEmbedding(model_name=model_name, cache_dir=cache_root)


def embedding_size(settings: Settings) -> int:
    from fastembed import TextEmbedding

    return TextEmbedding.get_embedding_size(settings.embedding_model)


def _embed_sync(texts: list[str], settings: Settings, as_query: bool) -> list[list[float]]:
    model = _load_model(settings.embedding_model, str(settings.embedding_cache_root.resolve()))
    with _model_lock:
        vectors = list(model.query_embed(texts)) if as_query else list(model.passage_embed(texts))
    return [vector.tolist() for vector in vectors]


async def embed_texts(texts: list[str], settings: Settings, *, as_query: bool = False) -> list[list[float]]:
    if not texts:
        return []
    return await asyncio.to_thread(_embed_sync, texts, settings, as_query)
