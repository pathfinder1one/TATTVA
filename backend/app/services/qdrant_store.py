from qdrant_client import AsyncQdrantClient, models

from app.config import Settings
from app.services.embedding_service import embedding_size

PAYLOAD_INDEX_FIELDS = ("tenant_id", "case_id", "document_id", "source_hash", "index_version")


async def ensure_collection(client: AsyncQdrantClient, settings: Settings) -> None:
    if not await client.collection_exists(settings.qdrant_collection):
        await client.create_collection(
            collection_name=settings.qdrant_collection,
            vectors_config=models.VectorParams(size=embedding_size(settings), distance=models.Distance.COSINE),
        )
    for field_name in PAYLOAD_INDEX_FIELDS:
        await client.create_payload_index(
            collection_name=settings.qdrant_collection,
            field_name=field_name,
            field_schema=models.PayloadSchemaType.KEYWORD,
        )


async def upsert_chunks(
    client: AsyncQdrantClient,
    settings: Settings,
    chunks: list[dict],
    vectors: list[list[float]],
) -> None:
    if len(chunks) != len(vectors):
        raise ValueError("Each indexed chunk must have exactly one embedding.")
    points = [
        models.PointStruct(
            id=chunk["point_id"],
            vector=vector,
            payload={
                "tenant_id": chunk["tenant_id"],
                "case_id": chunk["case_id"],
                "document_id": chunk["document_id"],
                "chunk_id": chunk["chunk_id"],
                "source_hash": chunk["source_hash"],
                "index_version": chunk["index_version"],
                "unit_type": chunk["unit_type"],
                "unit_number": chunk["unit_number"],
            },
        )
        for chunk, vector in zip(chunks, vectors, strict=True)
    ]
    if points:
        await client.upsert(
            collection_name=settings.qdrant_collection,
            points=points,
            wait=True,
        )


async def search_chunks(
    client: AsyncQdrantClient,
    settings: Settings,
    vector: list[float],
    *,
    tenant_id: str,
    case_id: str,
    limit: int,
):
    return await client.query_points(
        collection_name=settings.qdrant_collection,
        query=vector,
        query_filter=models.Filter(
            must=[
                models.FieldCondition(key="tenant_id", match=models.MatchValue(value=tenant_id)),
                models.FieldCondition(key="case_id", match=models.MatchValue(value=case_id)),
            ]
        ),
        limit=limit,
        with_payload=True,
        with_vectors=False,
    )
