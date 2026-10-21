import asyncio

from fastapi import HTTPException
from pymongo.asynchronous.database import AsyncDatabase
from qdrant_client import AsyncQdrantClient

from app.config import Settings
from app.domain.enums import DocumentStatus
from app.repositories.chunks_repo import ChunksRepository
from app.repositories.documents_repo import DocumentsRepository
from app.schemas.responses import SearchCitation
from app.services.embedding_service import embed_texts
from app.services.qdrant_store import ensure_collection, search_chunks
from app.services.text_store import read_text_version


async def search_case(
    database: AsyncDatabase,
    qdrant: AsyncQdrantClient,
    settings: Settings,
    *,
    case_id: str,
    tenant_id: str,
    query: str,
    top_k: int,
) -> list[SearchCitation]:
    try:
        await ensure_collection(qdrant, settings)
        query_vector = (await embed_texts([query], settings, as_query=True))[0]
        response = await search_chunks(
            qdrant,
            settings,
            query_vector,
            tenant_id=tenant_id,
            case_id=case_id,
            limit=min(100, top_k * 5),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="Case retrieval is unavailable because a search dependency failed.",
        ) from exc

    chunks_repo = ChunksRepository(database)
    documents_repo = DocumentsRepository(database)
    citations: list[SearchCitation] = []
    text_versions: dict[tuple[str, str, str], str | None] = {}
    for point in response.points:
        payload = point.payload or {}
        # Defense in depth: verify the mandatory filters on each returned point.
        if payload.get("tenant_id") != tenant_id or payload.get("case_id") != case_id:
            continue
        chunk_id = payload.get("chunk_id")
        document_id = payload.get("document_id")
        index_version = payload.get("index_version")
        source_hash = payload.get("source_hash")
        if not all(isinstance(value, str) and value for value in (chunk_id, document_id, index_version, source_hash)):
            continue
        chunk = await chunks_repo.get_chunk(chunk_id, case_id, tenant_id)
        document = await documents_repo.get_for_case(document_id, case_id, tenant_id)
        if chunk is None or document is None:
            continue
        if (
            document.get("status") != DocumentStatus.INDEXED.value
            or document.get("active_index_version") != index_version
            or document.get("indexed_source_hash") != source_hash
            or chunk.get("index_version") != index_version
            or chunk.get("source_hash") != source_hash
        ):
            continue
        version_key = (document_id, source_hash, chunk["parser_version"])
        if version_key not in text_versions:
            version_metadata = await chunks_repo.get_version_for_index(
                document_id, source_hash, chunk["parser_version"], index_version
            )
            if version_metadata is None:
                text_versions[version_key] = None
            else:
                try:
                    text_versions[version_key] = await asyncio.to_thread(
                        read_text_version, settings, version_metadata["text_storage_key"]
                    )
                except (HTTPException, UnicodeError, OSError):
                    text_versions[version_key] = None
        text_version = text_versions[version_key]
        start_offset = chunk["start_offset"]
        end_offset = chunk["end_offset"]
        if (
            text_version is None
            or start_offset < 0
            or end_offset <= start_offset
            or end_offset > len(text_version)
        ):
            continue
        exact_span = text_version[start_offset:end_offset]
        if exact_span != chunk["text"]:
            continue
        unit_type = chunk["unit_type"]
        citations.append(
            SearchCitation(
                citation_id=f"cite_{chunk_id}",
                document_id=document_id,
                filename=document["filename"],
                chunk_id=chunk_id,
                source_hash=source_hash,
                parser_version=chunk["parser_version"],
                unit_type=unit_type,
                unit_number=chunk["unit_number"],
                start_offset=start_offset,
                end_offset=end_offset,
                text=exact_span,
                retrieval_score=float(point.score),
            )
        )
        if len(citations) >= top_k:
            break
    return citations
