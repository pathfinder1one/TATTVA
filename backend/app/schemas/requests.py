from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domain.enums import EntityType, ReviewStatus, VerificationDecision


class CaseCreateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    case_number: str = Field(min_length=1, max_length=80)
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=4000)


class CaseSearchRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    query: str = Field(min_length=2, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=20)


class SourceSpanInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    chunk_id: str = Field(min_length=1, max_length=100)
    start_offset: int = Field(ge=0)
    end_offset: int = Field(gt=0)

    @model_validator(mode="after")
    def validate_offset_order(self):
        if self.end_offset <= self.start_offset:
            raise ValueError("end_offset must be greater than start_offset")
        return self


class EntityCreateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    entity_type: EntityType
    display_name: str = Field(min_length=1, max_length=200)
    source_spans: list[SourceSpanInput] = Field(min_length=1, max_length=20)


class RelationshipCreateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    subject_entity_id: str = Field(min_length=1, max_length=100)
    predicate: str = Field(min_length=1, max_length=120)
    object_entity_id: str = Field(min_length=1, max_length=100)
    source_spans: list[SourceSpanInput] = Field(min_length=1, max_length=20)


class RelationshipVerificationRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    decision: VerificationDecision
    rationale: str = Field(min_length=3, max_length=2000)


class RelationshipReviewRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    decision: ReviewStatus
    rationale: str = Field(min_length=3, max_length=2000)


class FindingCreateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    finding_type: str = Field(pattern="^(relationship|contradiction|pattern|hypothesis)$")
    statement: str = Field(min_length=3, max_length=2000)
    evidence_ids: list[str] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def evidence_ids_unique(self):
        if len(set(self.evidence_ids)) != len(self.evidence_ids):
            raise ValueError("Evidence IDs must be unique.")
        return self


class FindingReviewRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    decision: ReviewStatus
    rationale: str = Field(min_length=3, max_length=2000)


class AnalysisRunCreateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    query: str = Field(min_length=2, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=20)
