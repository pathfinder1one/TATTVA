import asyncio
import hashlib
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from fastapi import HTTPException
from pymongo.asynchronous.database import AsyncDatabase
from qdrant_client import AsyncQdrantClient

from app.config import Settings
from app.domain.enums import DocumentStatus
from app.repositories.chunks_repo import ChunksRepository
from app.repositories.documents_repo import DocumentsRepository
from app.services.document_parser import PARSER_VERSION, parse_document, split_chunks
from app.services.embedding_service import embed_texts
from app.services.qdrant_store import ensure_collection, upsert_chunks
from app.services.text_store import write_text_version


async def index_document(
    database: AsyncDatabase,
    qdrant: AsyncQdrantClient,
    settings: Settings,
    document: dict,
) -> dict:
    documents = DocumentsRepository(database)
    document_id = document["document_id"]
    case_id = document["case_id"]
    tenant_id = document["tenant_id"]
    storage_key = document["storage_key"]
    if Path(storage_key).name != storage_key:
        raise HTTPException(status_code=422, detail="Document storage metadata is invalid.")
    file_path = Path(settings.file_storage_root).resolve() / storage_key
    if not file_path.is_file():
        raise HTTPException(status_code=410, detail="The stored source file is unavailable.")

    chunk_repo = ChunksRepository(database)
    keep_previous_index = bool(document.get("active_index_version"))
    if not keep_previous_index:
        await documents.mark_indexing(document_id, case_id, tenant_id)
    try:
        stored_hash = await asyncio.to_thread(_hash_file, file_path)
        if stored_hash != document["sha256"]:
            raise HTTPException(status_code=409, detail="Stored source hash does not match document metadata.")
        parsed = await asyncio.to_thread(
            parse_document, file_path, document["extension"], settings.max_document_chars
        )
        chunks_raw = split_chunks(
            parsed.text,
            parsed.units,
            settings.chunk_max_chars,
            settings.chunk_overlap_chars,
        )
        index_version = hashlib.sha256(
            f"{document_id}:{document['sha256']}:{PARSER_VERSION}".encode("utf-8")
        ).hexdigest()
        chunks = []
        for item in chunks_raw:
            chunk_id = "chunk_" + hashlib.sha256(
                f"{index_version}:{item['start_offset']}:{item['end_offset']}".encode("utf-8")
            ).hexdigest()
            point_id = str(uuid5(NAMESPACE_URL, chunk_id))
            chunks.append(
                {
                    **item,
                    "chunk_id": chunk_id,
                    "point_id": point_id,
                    "document_id": document_id,
                    "case_id": case_id,
                    "tenant_id": tenant_id,
                    "source_hash": document["sha256"],
                    "parser_version": PARSER_VERSION,
                    "index_version": index_version,
                    "created_at": document["created_at"],
                }
            )

        text_storage_key = await asyncio.to_thread(
            write_text_version, settings, document_id, index_version, parsed.text
        )
        version = {
            "document_id": document_id,
            "case_id": case_id,
            "tenant_id": tenant_id,
            "source_hash": document["sha256"],
            "parser_version": PARSER_VERSION,
            "index_version": index_version,
            "text_storage_key": text_storage_key,
            "text_length": len(parsed.text),
            "units": parsed.units,
            "chunk_count": len(chunks),
        }
        await chunk_repo.save_version(version)
        await chunk_repo.save_chunks(chunks)

        await ensure_collection(qdrant, settings)
        vectors = await embed_texts([item["text"] for item in chunks], settings)
        await upsert_chunks(qdrant, settings, chunks, vectors)
        await documents.mark_indexed(
            document_id,
            case_id,
            tenant_id,
            source_hash=document["sha256"],
            parser_version=PARSER_VERSION,
            index_version=index_version,
        )
        return {
            "document_id": document_id,
            "status": DocumentStatus.INDEXED,
            "source_hash": document["sha256"],
            "parser_version": PARSER_VERSION,
            "index_version": index_version,
            "chunk_count": len(chunks),
            "character_count": len(parsed.text),
        }
    except HTTPException:
        await documents.record_indexing_failure(
            document_id, case_id, tenant_id, keep_previous_index=keep_previous_index
        )
        raise
    except Exception as exc:
        await documents.record_indexing_failure(
            document_id, case_id, tenant_id, keep_previous_index=keep_previous_index
        )
        raise HTTPException(
            status_code=503,
            detail="Document indexing failed because a processing dependency is unavailable. Retry safely.",
        ) from exc


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()
