from datetime import datetime, timezone
from uuid import uuid4

from fastapi import HTTPException, status
from pymongo.asynchronous.database import AsyncDatabase

from app.dependencies import Actor
from app.domain.enums import ReviewStatus
from app.domain.finding import FindingRecord
from app.repositories.audit_repo import AuditRepository
from app.repositories.evidence_repo import EvidenceRepository
from app.repositories.findings_repo import FindingsRepository
from app.repositories.memberships_repo import MembershipsRepository
from app.schemas.requests import FindingCreateRequest
from app.services.evidence_validator import revalidate_evidence


async def create_finding_candidate(
    database: AsyncDatabase, settings, actor: Actor, case_id: str, request: FindingCreateRequest
) -> FindingRecord:
    evidence_repo = EvidenceRepository(database)
    evidence = await evidence_repo.get_many(request.evidence_ids, case_id, actor.tenant_id)
    if len(evidence) != len(request.evidence_ids):
        raise HTTPException(status_code=422, detail="Finding evidence must belong to this case.")
    for item in evidence:
        if not await revalidate_evidence(database, settings, item):
            raise HTTPException(status_code=409, detail="Finding evidence no longer resolves to the current source.")

    now = datetime.now(timezone.utc)
    record = FindingRecord(
        finding_id=f"finding_{uuid4().hex}",
        case_id=case_id,
        tenant_id=actor.tenant_id,
        finding_type=request.finding_type,
        statement=request.statement,
        evidence_ids=request.evidence_ids,
        created_by=actor.user_id,
        created_at=now,
        updated_at=now,
    )
    repository = FindingsRepository(database)
    await repository.create(record.to_document())
    try:
        await AuditRepository(database).append({
            "event_id": f"audit_{uuid4().hex}",
            "case_id": case_id,
            "tenant_id": actor.tenant_id,
            "actor_id": actor.user_id,
            "action": "finding.candidate_created",
            "target_type": "finding",
            "target_id": record.finding_id,
            "timestamp": now,
            "result": "success",
        })
    except Exception:
        await repository.remove(case_id, record.finding_id)
        raise
    return record


async def review_finding(
    database: AsyncDatabase, settings, actor: Actor, case_id: str, finding_id: str,
    decision: ReviewStatus, rationale: str,
) -> dict:
    membership = MembershipsRepository(database)
    role = await membership.get_role(
        case_id=case_id, tenant_id=actor.tenant_id, user_id=actor.user_id
    )
    if role not in {"owner", "reviewer"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="A case reviewer role is required.")
    if decision == ReviewStatus.NOT_REVIEWED:
        raise HTTPException(status_code=422, detail="A review decision must be provided.")

    repository = FindingsRepository(database)
    record = await repository.get_for_case(finding_id, case_id, actor.tenant_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Finding not found.")
    evidence = await EvidenceRepository(database).get_many(record["evidence_ids"], case_id, actor.tenant_id)
    if len(evidence) != len(record["evidence_ids"]):
        raise HTTPException(status_code=409, detail="Finding evidence is incomplete.")
    for item in evidence:
        if not await revalidate_evidence(database, settings, item):
            raise HTTPException(status_code=409, detail="Finding evidence no longer resolves to the current source.")

    now = datetime.now(timezone.utc)
    updated = await repository.set_review(
        finding_id,
        case_id,
        actor.tenant_id,
        expected_status=record["review_status"],
        decision=decision.value,
        rationale=rationale,
        reviewer_id=actor.user_id,
        updated_at=now,
    )
    if updated is None:
        raise HTTPException(status_code=409, detail="Finding review changed concurrently; reload and retry.")
    await AuditRepository(database).append({
        "event_id": f"audit_{uuid4().hex}",
        "case_id": case_id,
        "tenant_id": actor.tenant_id,
        "actor_id": actor.user_id,
        "action": "finding.review_changed",
        "target_type": "finding",
        "target_id": finding_id,
        "timestamp": now,
        "previous_status": record["review_status"],
        "new_status": decision.value,
        "rationale": rationale,
        "result": "success",
    })
    return updated
