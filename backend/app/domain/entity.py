from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.domain.enums import EntityType


class EntityRecord(BaseModel):
    entity_id: str
    case_id: str
    tenant_id: str
    entity_type: EntityType
    display_name: str
    normalized_name: str
    created_by: str
    created_at: datetime

    def to_document(self) -> dict[str, Any]:
        return self.model_dump(mode="python")
