from datetime import datetime, timezone
from uuid import uuid4

from fastapi import HTTPException, status
from pymongo.asynchronous.database import AsyncDatabase

from app.dependencies import Actor
from app.domain.enums import ReviewStatus, VerificationDecision, VerificationStatus
from app.domain.relationship import RelationshipRecord
from app.repositories.audit_repo import AuditRepository
from app.repositories.entities_repo import EntitiesRepository
from app.repositories.evidence_repo import EvidenceRepository
from app.repositories.memberships_repo import MembershipsRepository
from app.repositories.relationships_repo import RelationshipsRepository
from app.schemas.requests import RelationshipCreateRequest
from app.services.evidence_validator import create_evidence_records, revalidate_evidence


async def create_relationship(database: AsyncDatabase, settings, actor: Actor, case_id: str, request: RelationshipCreateRequest):
    if request.subject_entity_id == request.object_entity_id:
        raise HTTPException(status_code=422, detail="A relationship must connect two different entities.")
    entities = await EntitiesRepository(database).get_many(
        [request.subject_entity_id, request.object_entity_id], case_id, actor.tenant_id
    )
    if len(entities) != 2:
        raise HTTPException(status_code=404, detail="One or more case entities were not found.")

    now = datetime.now(timezone.utc)
    relationship_id = f"relationship_{uuid4().hex}"
    evidence_records = await create_evidence_records(
        database, settings, actor, case_id, request.source_spans, "relationship_claim"
    )
    record = RelationshipRecord(
        relationship_id=relationship_id,
        case_id=case_id,
        tenant_id=actor.tenant_id,
        subject_entity_id=request.subject_entity_id,
        predicate=request.predicate,
        object_entity_id=request.object_entity_id,
        evidence_ids=[evidence.evidence_id for evidence in evidence_records],
        verification_status=VerificationStatus.CANDIDATE,
        verification_rationale="Candidate only; a reviewer must assess predicate-specific source support.",
        created_by=actor.user_id,
        created_at=now,
        updated_at=now,
    )
    relationships = RelationshipsRepository(database)
    try:
        await relationships.create(record.to_document())
        await AuditRepository(database).append(
            {
                "event_id": f"audit_{uuid4().hex}",
                "case_id": case_id,
                "tenant_id": actor.tenant_id,
                "actor_id": actor.user_id,
                "action": "relationship.candidate_created",
                "target_type": "relationship",
                "target_id": relationship_id,
                "timestamp": now,
                "result": "success",
            }
        )
    except Exception:
        await relationships.remove(case_id, relationship_id)
        for evidence in evidence_records:
            await EvidenceRepository(database).remove(case_id, evidence.evidence_id)
        raise
    return record


async def set_relationship_verification(
    database: AsyncDatabase,
    settings,
    actor: Actor,
    case_id: str,
    relationship_id: str,
    decision: VerificationDecision,
    rationale: str,
):
    await _require_reviewer(database, actor, case_id)
    relationships = RelationshipsRepository(database)
    record = await relationships.get_for_case(relationship_id, case_id, actor.tenant_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Relationship not found.")
    evidence = await EvidenceRepository(database).get_many(
        record["evidence_ids"], case_id, actor.tenant_id
    )
    if len(evidence) != len(record["evidence_ids"]):
        raise HTTPException(status_code=409, detail="Relationship evidence is incomplete.")
    for item in evidence:
        if not await revalidate_evidence(database, settings, item):
            raise HTTPException(status_code=409, detail="Relationship evidence no longer resolves to the current source.")

    now = datetime.now(timezone.utc)
    updated = await relationships.set_verification(
        relationship_id,
        case_id,
        actor.tenant_id,
        decision=decision.value,
        rationale=rationale,
        updated_at=now,
    )
    if updated is None:
        raise HTTPException(status_code=404, detail="Relationship not found.")
    await AuditRepository(database).append(
        {
            "event_id": f"audit_{uuid4().hex}",
            "case_id": case_id,
            "tenant_id": actor.tenant_id,
            "actor_id": actor.user_id,
            "action": "relationship.verification_changed",
            "target_type": "relationship",
            "target_id": relationship_id,
            "timestamp": now,
            "previous_status": record["verification_status"],
            "new_status": decision.value,
            "rationale": rationale,
            "result": "success",
        }
    )
    return updated


async def set_relationship_review(
    database: AsyncDatabase,
    actor: Actor,
    case_id: str,
    relationship_id: str,
    decision: ReviewStatus,
    rationale: str,
):
    await _require_reviewer(database, actor, case_id)
    relationships = RelationshipsRepository(database)
    record = await relationships.get_for_case(relationship_id, case_id, actor.tenant_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Relationship not found.")
    if decision == ReviewStatus.ACCEPTED_FOR_REPORT and record["verification_status"] != VerificationStatus.SUPPORTED.value:
        raise HTTPException(
            status_code=409,
            detail="A relationship must be verified as supported before it can be accepted for a report.",
        )
    now = datetime.now(timezone.utc)
    updated = await relationships.set_review(
        relationship_id,
        case_id,
        actor.tenant_id,
        decision=decision.value,
        rationale=rationale,
        updated_at=now,
    )
    if updated is None:
        raise HTTPException(status_code=404, detail="Relationship not found.")
    await AuditRepository(database).append(
        {
            "event_id": f"audit_{uuid4().hex}",
            "case_id": case_id,
            "tenant_id": actor.tenant_id,
            "actor_id": actor.user_id,
            "action": "relationship.review_changed",
            "target_type": "relationship",
            "target_id": relationship_id,
            "timestamp": now,
            "previous_status": record["review_status"],
            "new_status": decision.value,
            "rationale": rationale,
            "result": "success",
        }
    )
    return updated


async def _require_reviewer(database: AsyncDatabase, actor: Actor, case_id: str) -> None:
    role = await MembershipsRepository(database).get_role(
        case_id=case_id, tenant_id=actor.tenant_id, user_id=actor.user_id
    )
    if role not in {"owner", "reviewer"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="A case reviewer role is required.")
