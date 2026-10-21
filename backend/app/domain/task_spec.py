from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class TaskType(StrEnum):
    RETRIEVE_SOURCES = "retrieve_sources"
    EXTRACT_CANDIDATES = "extract_candidates"
    ANALYZE_GRAPH_PATTERNS = "analyze_graph_patterns"
    COMPARE_CANDIDATES = "compare_candidates"
    SUGGEST_HYPOTHESES = "suggest_hypotheses"


class TaskStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


class TaskSpec(BaseModel):
    """Strict, bounded task contract; task types are dispatched through an allowlist."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    task_id: str = Field(min_length=1, max_length=120)
    task_type: TaskType
    inputs: dict[str, Any] = Field(default_factory=dict)
    depends_on: list[str] = Field(default_factory=list, max_length=20)
    timeout_seconds: int = Field(default=45, ge=1, le=600)
    retry_limit: int = Field(default=0, ge=0, le=3)

    @model_validator(mode="after")
    def validate_dependencies(self):
        if self.task_id in self.depends_on:
            raise ValueError("A task cannot depend on itself.")
        if len(set(self.depends_on)) != len(self.depends_on):
            raise ValueError("Task dependencies must be unique.")
        return self
