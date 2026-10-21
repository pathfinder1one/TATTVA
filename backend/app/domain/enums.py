from enum import StrEnum


class DocumentStatus(StrEnum):
    UPLOADED = "uploaded"
    INDEXING = "indexing"
    INDEXED = "indexed"
    INDEXING_FAILED = "indexing_failed"
    QUARANTINED = "quarantined"


class RunStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    AWAITING_REVIEW = "awaiting_review"
    COMPLETED = "completed"
    COMPLETED_WITH_WARNINGS = "completed_with_warnings"
    FAILED = "failed"
    CANCEL_REQUESTED = "cancel_requested"
    CANCELLED = "cancelled"


class VerificationStatus(StrEnum):
    CANDIDATE = "candidate"
    SUPPORTED = "supported"
    DISPUTED = "disputed"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    VERIFICATION_FAILED = "verification_failed"


class VerificationDecision(StrEnum):
    SUPPORTED = "supported"
    DISPUTED = "disputed"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class ReviewStatus(StrEnum):
    NOT_REVIEWED = "not_reviewed"
    ACCEPTED_FOR_REPORT = "accepted_for_report"
    REJECTED = "rejected"
    NEEDS_MORE_EVIDENCE = "needs_more_evidence"


class EntityType(StrEnum):
    PERSON = "person"
    ORGANIZATION = "organization"
    PHONE = "phone"
    EMAIL = "email"
    ADDRESS = "address"
    VEHICLE = "vehicle"
    ACCOUNT = "account"
    EVENT = "event"
    LOCATION = "location"
    DEVICE = "device"
    OTHER = "other"
