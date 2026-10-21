from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.domain.enums import DocumentStatus


class DocumentRecord(BaseModel):
    document_id: str
    case_id: str
    tenant_id: str
    filename: str
    media_type: str
    extension: str
    size_bytes: int
    sha256: str
    storage_key: str
    status: DocumentStatus = DocumentStatus.UPLOADED
    parser_version: str | None = None
    indexed_source_hash: str | None = None
    active_index_version: str | None = None
    created_by: str
    created_at: datetime

    def to_document(self) -> dict[str, Any]:
        return self.model_dump(mode="python")
