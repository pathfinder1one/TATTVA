from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import RunStatus


class AnalysisRunRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    case_id: str
    tenant_id: str
    created_by: str
    idempotency_key: str | None = None
    request_fingerprint: str | None = None
    query: str = Field(min_length=2, max_length=2000)
    status: RunStatus = RunStatus.QUEUED
    queue_ready: bool = False
    task_count: int = Field(ge=1)
    result_summary: dict[str, Any] = Field(default_factory=dict)
    event_seq: int = 0
    created_at: datetime
    updated_at: datetime

    def to_document(self) -> dict[str, Any]:
        return self.model_dump(mode="python")
