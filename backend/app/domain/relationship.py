from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.domain.enums import ReviewStatus, VerificationStatus


class RelationshipRecord(BaseModel):
    relationship_id: str
    case_id: str
    tenant_id: str
    subject_entity_id: str
    predicate: str
    object_entity_id: str
    evidence_ids: list[str]
    verification_status: VerificationStatus
    verification_rationale: str | None = None
    review_status: ReviewStatus = ReviewStatus.NOT_REVIEWED
    created_by: str
    created_at: datetime
    updated_at: datetime

    def to_document(self) -> dict[str, Any]:
        return self.model_dump(mode="python")
