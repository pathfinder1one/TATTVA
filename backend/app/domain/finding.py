from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import ReviewStatus


class FindingRecord(BaseModel):
    """A source-linked candidate finding; acceptance remains a separate human action."""

    model_config = ConfigDict(extra="forbid")

    finding_id: str = Field(min_length=1, max_length=120)
    case_id: str = Field(min_length=1, max_length=120)
    tenant_id: str = Field(min_length=1, max_length=120)
    finding_type: Literal["relationship", "contradiction", "pattern", "hypothesis"]
    statement: str = Field(min_length=3, max_length=2000)
    evidence_ids: list[str] = Field(min_length=1, max_length=100)
    review_status: ReviewStatus = ReviewStatus.NOT_REVIEWED
    review_rationale: str | None = Field(default=None, max_length=2000)
    reviewed_by: str | None = Field(default=None, max_length=120)
    created_by: str = Field(min_length=1, max_length=120)
    created_at: datetime
    updated_at: datetime

    def to_document(self) -> dict[str, Any]:
        return self.model_dump(mode="python")
