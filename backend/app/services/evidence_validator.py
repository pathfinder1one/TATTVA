import asyncio
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import HTTPException
from pymongo.asynchronous.database import AsyncDatabase

from app.config import Settings
from app.dependencies import Actor
from app.domain.evidence import EvidenceRecord
from app.repositories.evidence_repo import EvidenceRepository
from app.schemas.requests import SourceSpanInput
from app.domain.enums import DocumentStatus
from app.repositories.chunks_repo import ChunksRepository
from app.repositories.documents_repo import DocumentsRepository
from app.services.text_store import read_text_version


async def resolve_source_span(
    database: AsyncDatabase,
    settings: Settings,
    tenant_id: str,
    case_id: str,
    chunk_id: str,
    start_offset: int,
    end_offset: int,
) -> tuple[dict, dict, str]:
    chunk = await ChunksRepository(database).get_chunk(chunk_id, case_id, tenant_id)
    if chunk is None:
        raise HTTPException(status_code=422, detail="Source span is not available in this case.")
    document = await DocumentsRepository(database).get_for_case(
        chunk["document_id"], case_id, tenant_id
    )
    if (
        document is None
        or document.get("status") != DocumentStatus.INDEXED.value
        or document.get("active_index_version") != chunk.get("index_version")
        or document.get("indexed_source_hash") != chunk.get("source_hash")
    ):
        raise HTTPException(status_code=422, detail="Source span is not part of the current indexed version.")
    if start_offset < chunk["start_offset"] or end_offset > chunk["end_offset"] or end_offset <= start_offset:
        raise HTTPException(status_code=422, detail="Source offsets must fit within the cited chunk.")
    version = await ChunksRepository(database).get_version_for_index(
        chunk["document_id"], chunk["source_hash"], chunk["parser_version"], chunk["index_version"]
    )
    if version is None:
        raise HTTPException(status_code=422, detail="Source text version is unavailable.")
    text = await asyncio.to_thread(read_text_version, settings, version["text_storage_key"])
    if end_offset > len(text) or text[start_offset:end_offset] != chunk["text"][
        start_offset - chunk["start_offset"] : end_offset - chunk["start_offset"]
    ]:
        raise HTTPException(status_code=422, detail="Source offsets do not resolve to the indexed text.")
    return chunk, document, text[start_offset:end_offset]


async def revalidate_evidence(database: AsyncDatabase, settings: Settings, evidence: dict) -> bool:
    try:
        chunks = ChunksRepository(database)
        chunk = await chunks.get_chunk(evidence["chunk_id"], evidence["case_id"], evidence["tenant_id"])
        document = await DocumentsRepository(database).get_for_case(
            evidence["document_id"], evidence["case_id"], evidence["tenant_id"]
        )
        if chunk is None or document is None:
            return False
        if (
            chunk["document_id"] != evidence["document_id"]
            or chunk["source_hash"] != evidence["source_hash"]
            or chunk["parser_version"] != evidence["parser_version"]
            or chunk["index_version"] != evidence["index_version"]
            or document["sha256"] != evidence["source_hash"]
        ):
            return False
        start = evidence["start_offset"]
        end = evidence["end_offset"]
        if start < chunk["start_offset"] or end > chunk["end_offset"] or end <= start:
            return False
        version = await chunks.get_version_for_index(
            evidence["document_id"], evidence["source_hash"], evidence["parser_version"], evidence["index_version"]
        )
        if version is None:
            return False
        text = await asyncio.to_thread(read_text_version, settings, version["text_storage_key"])
        if end > len(text) or text[start:end] != evidence["quote"]:
            return False
        chunk_quote = chunk["text"][start - chunk["start_offset"] : end - chunk["start_offset"]]
        return (
            chunk_quote == evidence["quote"]
        )
    except (HTTPException, UnicodeError, OSError, KeyError):
        return False


async def create_evidence_records(
    database: AsyncDatabase,
    settings: Settings,
    actor: Actor,
    case_id: str,
    source_spans: list[SourceSpanInput],
    evidence_type: str,
) -> list[EvidenceRecord]:
    repo = EvidenceRepository(database)
    created: list[EvidenceRecord] = []
    try:
        for source_span in source_spans:
            chunk, _document, quote = await resolve_source_span(
                database,
                settings,
                actor.tenant_id,
                case_id,
                source_span.chunk_id,
                source_span.start_offset,
                source_span.end_offset,
            )
            record = EvidenceRecord(
                evidence_id=f"evidence_{uuid4().hex}",
                case_id=case_id,
                tenant_id=actor.tenant_id,
                document_id=chunk["document_id"],
                chunk_id=chunk["chunk_id"],
                source_hash=chunk["source_hash"],
                parser_version=chunk["parser_version"],
                index_version=chunk["index_version"],
                evidence_type=evidence_type,
                start_offset=source_span.start_offset,
                end_offset=source_span.end_offset,
                quote=quote,
                created_by=actor.user_id,
                created_at=datetime.now(timezone.utc),
            )
            await repo.create(record.to_document())
            created.append(record)
        return created
    except Exception:
        for record in created:
            await repo.remove(case_id, record.evidence_id)
        raise
