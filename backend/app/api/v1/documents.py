from datetime import datetime, timezone
import asyncio
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from pymongo.asynchronous.database import AsyncDatabase

from app.config import Settings, get_settings
from app.dependencies import Actor, get_actor, get_database
from app.domain.document import DocumentRecord
from app.domain.enums import DocumentStatus
from app.repositories.documents_repo import DocumentsRepository
from app.repositories.chunks_repo import ChunksRepository
from app.schemas.responses import DocumentResponse, IndexDocumentResponse, SourceSpanResponse
from app.services.case_access import require_case_access
from app.services.file_storage import delete_stored_file, store_upload
from app.services.ingestion_service import index_document
from app.services.text_store import read_text_version

router = APIRouter(prefix="/cases/{case_id}/documents", tags=["documents"])


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    case_id: str,
    file: UploadFile = File(...),
    actor: Actor = Depends(get_actor),
    database: AsyncDatabase = Depends(get_database),
    settings: Settings = Depends(get_settings),
):
    await require_case_access(database, actor, case_id)
    storage_key, size, sha256, extension = await store_upload(file, settings)
    record = DocumentRecord(
        document_id=f"doc_{uuid4().hex}",
        case_id=case_id,
        tenant_id=actor.tenant_id,
        filename=(file.filename or "upload").split("/")[-1].split("\\")[-1],
        media_type=file.content_type or "application/octet-stream",
        extension=extension,
        size_bytes=size,
        sha256=sha256,
        storage_key=storage_key,
        status=DocumentStatus.UPLOADED,
        created_by=actor.user_id,
        created_at=datetime.now(timezone.utc),
    )
    try:
        await DocumentsRepository(database).create(record.to_document())
    except Exception:
        delete_stored_file(settings, storage_key)
        raise
    return record


@router.get("", response_model=list[DocumentResponse])
async def list_documents(
    case_id: str,
    actor: Actor = Depends(get_actor),
    database: AsyncDatabase = Depends(get_database),
):
    await require_case_access(database, actor, case_id)
    return await DocumentsRepository(database).list_for_case(case_id, actor.tenant_id)


@router.post("/{document_id}/index", response_model=IndexDocumentResponse)
async def post_document_index(
    document_id: str,
    request: Request,
    case_id: str,
    actor: Actor = Depends(get_actor),
    database: AsyncDatabase = Depends(get_database),
    settings: Settings = Depends(get_settings),
):
    await require_case_access(database, actor, case_id)
    document = await DocumentsRepository(database).get_for_case(document_id, case_id, actor.tenant_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    result = await index_document(database, request.app.state.qdrant, settings, document)
    request.app.state.qdrant_ready = True
    return result


@router.get("/{document_id}/chunks/{chunk_id}", response_model=SourceSpanResponse)
async def get_document_chunk(
    document_id: str,
    chunk_id: str,
    case_id: str,
    actor: Actor = Depends(get_actor),
    database: AsyncDatabase = Depends(get_database),
):
    await require_case_access(database, actor, case_id)
    documents = DocumentsRepository(database)
    document = await documents.get_for_case(document_id, case_id, actor.tenant_id)
    chunk = await ChunksRepository(database).get_chunk(chunk_id, case_id, actor.tenant_id)
    if (
        document is None
        or chunk is None
        or document.get("status") != DocumentStatus.INDEXED.value
        or document.get("active_index_version") != chunk.get("index_version")
        or document.get("indexed_source_hash") != chunk.get("source_hash")
        or chunk.get("document_id") != document_id
    ):
        raise HTTPException(status_code=404, detail="Source span not found.")
    version = await ChunksRepository(database).get_version_for_index(
        document_id,
        chunk["source_hash"],
        chunk["parser_version"],
        chunk["index_version"],
    )
    start_offset = chunk["start_offset"]
    end_offset = chunk["end_offset"]
    if (
        version is None
        or start_offset < 0
        or end_offset <= start_offset
        or end_offset > version["text_length"]
    ):
        raise HTTPException(status_code=404, detail="Source span not found.")
    exact_text = await asyncio.to_thread(read_text_version, get_settings(), version["text_storage_key"])
    if end_offset > len(exact_text) or exact_text[start_offset:end_offset] != chunk["text"]:
        raise HTTPException(status_code=404, detail="Source span not found.")
    return {
        **{key: chunk[key] for key in (
            "document_id", "chunk_id", "source_hash", "parser_version", "unit_type",
            "unit_number", "start_offset", "end_offset", "text"
        )},
        "filename": document["filename"],
    }
