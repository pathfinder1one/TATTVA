from datetime import datetime
from typing import Any

from pydantic import BaseModel


class EvidenceRecord(BaseModel):
    evidence_id: str
    case_id: str
    tenant_id: str
    document_id: str
    chunk_id: str
    source_hash: str
    parser_version: str
    index_version: str
    evidence_type: str
    start_offset: int
    end_offset: int
    quote: str
    created_by: str
    created_at: datetime

    def to_document(self) -> dict[str, Any]:
        return self.model_dump(mode="python")
