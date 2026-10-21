from datetime import datetime
from typing import Any

from pydantic import BaseModel


class CaseRecord(BaseModel):
    case_id: str
    tenant_id: str
    case_number: str
    title: str
    description: str | None = None
    created_by: str
    created_at: datetime
    updated_at: datetime

    def to_document(self) -> dict[str, Any]:
        return self.model_dump(mode="python")
