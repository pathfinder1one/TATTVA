from datetime import datetime, timezone
import hashlib
import json
import re
from uuid import uuid4

from pymongo.asynchronous.database import AsyncDatabase
from pymongo.errors import DuplicateKeyError
from fastapi import HTTPException, status

from app.config import Settings
from app.dependencies import Actor
from app.domain.analysis_run import AnalysisRunRecord
from app.domain.enums import RunStatus
from app.domain.task_spec import TaskStatus
from app.orchestrator.event_publisher import RunEventPublisher
from app.orchestrator.planner import plan_analysis
from app.repositories.audit_repo import AuditRepository
from app.repositories.runs_repo import RunsRepository
from app.schemas.requests import AnalysisRunCreateRequest


def validate_idempotency_key(key: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9._:-]{8,128}", key):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Idempotency-Key must contain 8 to 128 safe characters.",
        )
    return key


def request_fingerprint(body: AnalysisRunCreateRequest) -> str:
    payload = json.dumps(body.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def require_matching_idempotent_request(existing: dict, fingerprint: str) -> None:
    if existing.get("request_fingerprint") != fingerprint:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Idempotency-Key was already used with a different analysis request.",
        )


async def enqueue_analysis_run(
    database: AsyncDatabase, settings: Settings, actor: Actor, case_id: str,
    body: AnalysisRunCreateRequest, *, idempotency_key: str,
) -> tuple[dict, list[dict]]:
    validate_idempotency_key(idempotency_key)
    fingerprint = request_fingerprint(body)
    repository = RunsRepository(database)
    existing = await repository.get_by_idempotency_key(
        idempotency_key, case_id, actor.tenant_id, actor.user_id
    )
    if existing is not None:
        require_matching_idempotent_request(existing, fingerprint)
        tasks = await repository.list_tasks(existing["run_id"], case_id, actor.tenant_id)
        return existing, tasks

    specs = plan_analysis(body.query, body.top_k, settings)
    now = datetime.now(timezone.utc)
    run = AnalysisRunRecord(
        run_id=f"run_{uuid4().hex}", case_id=case_id, tenant_id=actor.tenant_id,
        created_by=actor.user_id, idempotency_key=idempotency_key,
        request_fingerprint=fingerprint, query=body.query, status=RunStatus.QUEUED,
        task_count=len(specs), result_summary={"stage": "retrieval_only"},
        created_at=now, updated_at=now,
    )
    tasks = [{
        "task_id": spec.task_id, "run_id": run.run_id, "case_id": case_id,
        "tenant_id": actor.tenant_id, "task_type": spec.task_type.value,
        "ordinal": index, "depends_on": spec.depends_on,
        "spec": spec.model_dump(mode="json"), "status": TaskStatus.QUEUED.value,
        "attempts": 0, "output": None, "error_code": None,
        "created_at": now, "updated_at": now,
    } for index, spec in enumerate(specs)]
    try:
        await repository.create(run.to_document(), tasks)
    except DuplicateKeyError:
        existing = await repository.get_by_idempotency_key(
            idempotency_key, case_id, actor.tenant_id, actor.user_id
        )
        if existing is None:
            raise
        require_matching_idempotent_request(existing, fingerprint)
        existing_tasks = await repository.list_tasks(existing["run_id"], case_id, actor.tenant_id)
        return existing, existing_tasks
    try:
        await RunEventPublisher(database).publish(
            run_id=run.run_id, case_id=case_id, tenant_id=actor.tenant_id,
            event_type="run.queued", payload={"status": RunStatus.QUEUED.value, "task_count": len(specs)},
        )
        await AuditRepository(database).append({
            "event_id": f"audit_{uuid4().hex}", "case_id": case_id,
            "tenant_id": actor.tenant_id, "actor_id": actor.user_id,
            "action": "analysis_run.created", "target_type": "analysis_run",
            "target_id": run.run_id, "timestamp": now, "result": "success",
        })
        activated = await repository.activate_run(run.run_id, case_id, actor.tenant_id, now)
        if activated is None:
            raise RuntimeError("Analysis run could not be activated.")
    except Exception:
        await repository.fail_unactivated_run(
            run.run_id, case_id, actor.tenant_id, datetime.now(timezone.utc)
        )
        raise
    return activated, tasks
