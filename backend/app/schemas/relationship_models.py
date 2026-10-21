from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class RelationshipClaim(BaseModel):
    """Unverified source-linked relationship suggestion."""

    model_config = ConfigDict(extra="forbid")

    subject_name: str = Field(min_length=1, max_length=200)
    predicate: str = Field(min_length=1, max_length=120)
    object_name: str = Field(min_length=1, max_length=200)
    citation_id: str = Field(min_length=1, max_length=140)
    quote: str = Field(min_length=1, max_length=2000)
    start_offset: int = Field(ge=0)
    end_offset: int = Field(gt=0)


class VerificationAssessment(BaseModel):
    """Advisory source check; only the human API can set a verification decision."""

    model_config = ConfigDict(extra="forbid")

    outcome: Literal["candidate", "insufficient_evidence"]
    rationale: str = Field(min_length=3, max_length=1000)
    evidence_ids: list[str] = Field(default_factory=list, max_length=100)
