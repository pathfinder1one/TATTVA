import asyncio
import json
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from pymongo.asynchronous.database import AsyncDatabase

from app.config import Settings, get_settings
from app.dependencies import Actor, get_actor, get_database
from app.domain.enums import RunStatus
from app.orchestrator.event_publisher import RunEventPublisher
from app.repositories.audit_repo import AuditRepository
from app.repositories.events_repo import RunEventsRepository
from app.repositories.runs_repo import RunsRepository
from app.schemas.requests import AnalysisRunCreateRequest
from app.schemas.responses import AnalysisRunResponse, AnalysisTaskResponse, RunEventResponse
from app.services.case_access import require_case_access
from app.services.analysis_run_service import enqueue_analysis_run

router = APIRouter(prefix="/cases/{case_id}/analysis-runs", tags=["analysis runs"])


@router.post("", response_model=AnalysisRunResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_analysis_run(
    case_id: str,
    body: AnalysisRunCreateRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=8, max_length=128),
    actor: Actor = Depends(get_actor),
    database: AsyncDatabase = Depends(get_database),
    settings: Settings = Depends(get_settings),
):
    await require_case_access(database, actor, case_id)
    activated, task_records = await enqueue_analysis_run(
        database, settings, actor, case_id, body, idempotency_key=idempotency_key
    )
    return _run_response(activated, task_records)


@router.get("", response_model=list[AnalysisRunResponse])
async def list_analysis_runs(
    case_id: str,
    actor: Actor = Depends(get_actor),
    database: AsyncDatabase = Depends(get_database),
):
    await require_case_access(database, actor, case_id)
    records = await RunsRepository(database).list_for_case(case_id, actor.tenant_id)
    return [_run_response(record, []) for record in records]


@router.get("/{run_id}", response_model=AnalysisRunResponse)
async def get_analysis_run(
    case_id: str,
    run_id: str,
    actor: Actor = Depends(get_actor),
    database: AsyncDatabase = Depends(get_database),
):
    await require_case_access(database, actor, case_id)
    repository = RunsRepository(database)
    record = await repository.get_for_case(run_id, case_id, actor.tenant_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Analysis run not found.")
    tasks = await repository.list_tasks(run_id, case_id, actor.tenant_id)
    return _run_response(record, tasks)


@router.post("/{run_id}/cancel", response_model=AnalysisRunResponse)
async def cancel_analysis_run(
    case_id: str,
    run_id: str,
    actor: Actor = Depends(get_actor),
    database: AsyncDatabase = Depends(get_database),
):
    await require_case_access(database, actor, case_id)
    repository = RunsRepository(database)
    now = datetime.now(timezone.utc)
    updated = await repository.request_cancel(run_id, case_id, actor.tenant_id, now)
    if updated is None:
        existing = await repository.get_for_case(run_id, case_id, actor.tenant_id)
        if existing is None:
            raise HTTPException(status_code=404, detail="Analysis run not found.")
        raise HTTPException(status_code=409, detail="Analysis run cannot be cancelled in its current state.")
    if updated["status"] == RunStatus.CANCELLED.value:
        await repository.mark_queued_tasks_cancelled(run_id, case_id, actor.tenant_id, now)
        event_type = "run.cancelled"
    else:
        event_type = "run.cancel_requested"
    await RunEventPublisher(database).publish(
        run_id=run_id,
        case_id=case_id,
        tenant_id=actor.tenant_id,
        event_type=event_type,
        payload={"status": updated["status"]},
    )
    await AuditRepository(database).append(
        {
            "event_id": f"audit_{uuid4().hex}",
            "case_id": case_id,
            "tenant_id": actor.tenant_id,
            "actor_id": actor.user_id,
            "action": "analysis_run.cancelled" if updated["status"] == RunStatus.CANCELLED.value else "analysis_run.cancel_requested",
            "target_type": "analysis_run",
            "target_id": run_id,
            "timestamp": now,
            "result": "success",
        }
    )
    tasks = await repository.list_tasks(run_id, case_id, actor.tenant_id)
    return _run_response(updated, tasks)


@router.get("/{run_id}/events", response_model=list[RunEventResponse])
async def list_analysis_run_events(
    case_id: str,
    run_id: str,
    after_seq: int = 0,
    limit: int = 100,
    actor: Actor = Depends(get_actor),
    database: AsyncDatabase = Depends(get_database),
):
    await require_case_access(database, actor, case_id)
    if after_seq < 0 or limit < 1 or limit > 500:
        raise HTTPException(status_code=422, detail="Event cursor or page size is invalid.")
    run = await RunsRepository(database).get_for_case(run_id, case_id, actor.tenant_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Analysis run not found.")
    return await RunEventsRepository(database).list_after(
        run_id=run_id,
        case_id=case_id,
        tenant_id=actor.tenant_id,
        after_seq=after_seq,
        limit=limit,
    )


@router.get("/{run_id}/events/stream")
async def stream_analysis_run_events(
    case_id: str,
    run_id: str,
    request: Request,
    after_seq: int = 0,
    actor: Actor = Depends(get_actor),
    database: AsyncDatabase = Depends(get_database),
):
    await require_case_access(database, actor, case_id)
    if after_seq < 0:
        raise HTTPException(status_code=422, detail="Event cursor is invalid.")
    repository = RunsRepository(database)
    run = await repository.get_for_case(run_id, case_id, actor.tenant_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Analysis run not found.")

    async def event_stream():
        cursor = after_seq
        deadline = asyncio.get_running_loop().time() + 1800
        while asyncio.get_running_loop().time() < deadline:
            if await request.is_disconnected():
                return
            events = await RunEventsRepository(database).list_after(
                run_id=run_id, case_id=case_id, tenant_id=actor.tenant_id,
                after_seq=cursor, limit=100,
            )
            for event in events:
                cursor = event["seq"]
                public_event = RunEventResponse.model_validate(event).model_dump(mode="json")
                yield (
                    f"id: {cursor}\nevent: {event['type']}\ndata: "
                    f"{json.dumps(public_event, separators=(',', ':'))}\n\n"
                )
            latest = await repository.get_for_case(run_id, case_id, actor.tenant_id)
            if latest is None or latest["status"] in {
                RunStatus.COMPLETED.value, RunStatus.COMPLETED_WITH_WARNINGS.value,
                RunStatus.FAILED.value, RunStatus.CANCELLED.value,
            }:
                if not events:
                    return
            if not events:
                yield ": keep-alive\n\n"
            await asyncio.sleep(1)

    return StreamingResponse(
        event_stream(), media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def _run_response(run: dict, tasks: list[dict]) -> AnalysisRunResponse:
    return AnalysisRunResponse(
        run_id=run["run_id"],
        case_id=run["case_id"],
        status=run["status"],
        query=run["query"],
        task_count=run["task_count"],
        result_summary=run.get("result_summary", {}),
        created_by=run["created_by"],
        created_at=run["created_at"],
        updated_at=run["updated_at"],
        tasks=[
            AnalysisTaskResponse(
                task_id=task["task_id"],
                task_type=task["task_type"],
                status=task["status"],
                ordinal=task["ordinal"],
                depends_on=task.get("depends_on", []),
                attempts=task.get("attempts", 0),
                output=task.get("output"),
                error_code=task.get("error_code"),
                created_at=task["created_at"],
                updated_at=task["updated_at"],
            )
            for task in tasks
        ],
    )
