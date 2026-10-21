from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.enums import DocumentStatus, EntityType, ReviewStatus, VerificationStatus


class CaseResponse(BaseModel):
    case_id: str
    case_number: str
    title: str
    description: str | None
    created_by: str
    created_at: datetime
    updated_at: datetime


class DocumentResponse(BaseModel):
    document_id: str
    case_id: str
    filename: str
    media_type: str
    size_bytes: int
    sha256: str
    status: DocumentStatus
    created_by: str
    created_at: datetime


class IndexDocumentResponse(BaseModel):
    document_id: str
    status: DocumentStatus
    source_hash: str
    parser_version: str
    index_version: str
    chunk_count: int
    character_count: int


class SearchCitation(BaseModel):
    citation_id: str
    document_id: str
    filename: str
    chunk_id: str
    source_hash: str
    parser_version: str
    unit_type: str
    unit_number: int
    start_offset: int
    end_offset: int
    text: str
    retrieval_score: float
    score_type: str = "cosine_similarity"


class CaseSearchResponse(BaseModel):
    case_id: str
    query: str
    result_type: str = "retrieval_only"
    citations: list[SearchCitation]
    limitations: list[str]


class CaseAnswerResponse(BaseModel):
    case_id: str
    query: str
    answer: str
    citation_ids: list[str]
    citations: list[SearchCitation]
    insufficient_evidence: bool
    limitations: list[str]


class SourceSpanResponse(BaseModel):
    document_id: str
    filename: str
    chunk_id: str
    source_hash: str
    parser_version: str
    unit_type: str
    unit_number: int
    start_offset: int
    end_offset: int
    text: str


class EntityResponse(BaseModel):
    entity_id: str
    case_id: str
    entity_type: EntityType
    display_name: str
    created_by: str
    created_at: datetime
    evidence_ids: list[str] = Field(default_factory=list)


class RelationshipResponse(BaseModel):
    relationship_id: str
    case_id: str
    subject_entity_id: str
    predicate: str
    object_entity_id: str
    evidence_ids: list[str]
    verification_status: VerificationStatus
    verification_rationale: str | None = None
    review_status: ReviewStatus
    review_rationale: str | None = None
    created_by: str
    created_at: datetime
    updated_at: datetime


class CaseGraphResponse(BaseModel):
    case_id: str
    entities: list[EntityResponse]
    relationships: list[RelationshipResponse]
    metrics: dict[str, int | float]
    metrics_note: str
    integrity_flags: list[dict] = Field(default_factory=list)


class EvidenceResponse(BaseModel):
    evidence_id: str
    case_id: str
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


class FindingResponse(BaseModel):
    finding_id: str
    case_id: str
    finding_type: str
    statement: str
    evidence_ids: list[str]
    review_status: ReviewStatus
    review_rationale: str | None = None
    reviewed_by: str | None = None
    created_by: str
    created_at: datetime
    updated_at: datetime


class AnalysisTaskResponse(BaseModel):
    task_id: str
    task_type: str
    status: str
    ordinal: int
    depends_on: list[str]
    attempts: int
    output: dict | None = None
    error_code: str | None = None
    created_at: datetime
    updated_at: datetime


class AnalysisRunResponse(BaseModel):
    run_id: str
    case_id: str
    status: str
    query: str
    task_count: int
    result_summary: dict
    created_by: str
    created_at: datetime
    updated_at: datetime
    tasks: list[AnalysisTaskResponse] = Field(default_factory=list)


class RunEventResponse(BaseModel):
    event_id: str
    schema_version: int
    run_id: str
    seq: int
    type: str
    timestamp: datetime
    payload: dict
