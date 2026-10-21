import asyncio
import logging
from datetime import datetime, timezone
from uuid import uuid4

from pymongo.asynchronous.database import AsyncDatabase

from app.config import Settings
from app.domain.enums import RunStatus
from app.domain.task_spec import TaskSpec, TaskStatus
from app.orchestrator.event_publisher import RunEventPublisher
from app.orchestrator.executor import task_registry
from app.orchestrator.policies import validate_plan
from app.orchestrator.scheduler import ready_batches
from app.orchestrator.task_registry import TaskContext
from app.repositories.runs_repo import RunsRepository

logger = logging.getLogger("tattva.analysis_worker")


class TaskAttemptError(Exception):
    def __init__(self, cause: Exception, attempts: int):
        super().__init__(type(cause).__name__)
        self.cause = cause
        self.attempts = attempts


async def execute_analysis_run(
    database: AsyncDatabase,
    qdrant,
    settings: Settings,
    run_id: str,
    case_id: str,
    tenant_id: str,
    worker_id: str,
) -> None:
    """Run a persisted plan with bounded parallelism/retries and stable error codes."""
    runs = RunsRepository(database)
    events = RunEventPublisher(database)
    heartbeat = asyncio.create_task(
        _renew_lease(runs, run_id, worker_id, settings.worker_lease_seconds)
    )
    failed = False
    completed_outputs: dict[str, dict] = {}
    completed_ids: set[str] = set()
    failed_ids: set[str] = set()
    citation_count = 0
    try:
        await events.publish(
            run_id=run_id,
            case_id=case_id,
            tenant_id=tenant_id,
            event_type="run.started",
            payload={"status": RunStatus.RUNNING.value},
        )
        task_records = await runs.list_tasks(run_id, case_id, tenant_id)
        specs = [TaskSpec.model_validate(record["spec"]) for record in task_records]
        record_by_id = {record["task_id"]: record for record in task_records}
        for record in task_records:
            if record.get("status") == TaskStatus.COMPLETED.value and isinstance(record.get("output"), dict):
                completed_outputs[record["task_id"]] = record["output"]
                completed_ids.add(record["task_id"])
        citation_count = sum(len(value.get("citations", [])) for value in completed_outputs.values())
        validate_plan(specs, settings, task_registry)
        batches = ready_batches(specs, settings.max_concurrent_tasks)
        base_context = TaskContext(database, qdrant, settings, case_id, tenant_id, run_id)

        for batch in batches:
            if await runs.is_cancel_requested(run_id, case_id, tenant_id):
                break

            runnable = []
            for spec in batch:
                record = record_by_id.get(spec.task_id)
                if record is None:
                    raise ValueError("A planned task record is missing.")
                if record.get("status") == TaskStatus.COMPLETED.value:
                    continue
                if set(spec.depends_on) & failed_ids:
                    now = datetime.now(timezone.utc)
                    await runs.update_task(
                        run_id, spec.task_id, case_id, tenant_id,
                        {"status": TaskStatus.SKIPPED.value, "error_code": "dependency_failed", "updated_at": now},
                    )
                    failed_ids.add(spec.task_id)
                    failed = True
                    await events.publish(
                        run_id=run_id, case_id=case_id, tenant_id=tenant_id,
                        event_type="task.skipped", payload={"task_id": spec.task_id, "reason": "dependency_failed"},
                    )
                    continue
                now = datetime.now(timezone.utc)
                await runs.update_task(
                    run_id, spec.task_id, case_id, tenant_id,
                    {"status": TaskStatus.RUNNING.value, "updated_at": now},
                )
                await events.publish(
                    run_id=run_id, case_id=case_id, tenant_id=tenant_id,
                    event_type="task.started", payload={"task_id": spec.task_id, "task_type": spec.task_type.value},
                )
                missing_dependency_outputs = set(spec.depends_on) - completed_outputs.keys()
                if missing_dependency_outputs:
                    raise ValueError("A completed dependency output is unavailable.")
                task_context = TaskContext(
                    database=base_context.database,
                    qdrant=base_context.qdrant,
                    settings=base_context.settings,
                    case_id=base_context.case_id,
                    tenant_id=base_context.tenant_id,
                    run_id=base_context.run_id,
                    dependency_outputs={key: completed_outputs[key] for key in spec.depends_on},
                )
                runnable.append((spec, task_context))

            results = await asyncio.gather(
                *[_execute_with_retries(spec, task_context, settings) for spec, task_context in runnable],
                return_exceptions=True,
            )
            for (spec, _task_context), result in zip(runnable, results, strict=True):
                now = datetime.now(timezone.utc)
                if isinstance(result, Exception):
                    failed = True
                    failed_ids.add(spec.task_id)
                    cause = result.cause if isinstance(result, TaskAttemptError) else result
                    attempts = result.attempts if isinstance(result, TaskAttemptError) else 0
                    error_code = "task_timeout" if isinstance(cause, asyncio.TimeoutError) else "task_failed"
                    await runs.update_task(
                        run_id, spec.task_id, case_id, tenant_id,
                        {"status": TaskStatus.FAILED.value, "attempts": attempts, "error_code": error_code, "updated_at": now},
                    )
                    await events.publish(
                        run_id=run_id, case_id=case_id, tenant_id=tenant_id,
                        event_type="task.failed", payload={"task_id": spec.task_id, "error_code": error_code},
                    )
                    continue

                output, attempts = result
                await runs.update_task(
                    run_id, spec.task_id, case_id, tenant_id,
                    {
                        "status": TaskStatus.COMPLETED.value,
                        "attempts": attempts,
                        "output": output,
                        "updated_at": now,
                    },
                )
                completed_ids.add(spec.task_id)
                completed_outputs[spec.task_id] = output
                citation_count += len(output.get("citations", []))
                await events.publish(
                    run_id=run_id, case_id=case_id, tenant_id=tenant_id,
                    event_type="task.completed",
                    payload={
                        "task_id": spec.task_id,
                        "citation_count": len(output.get("citations", [])),
                        "mention_count": len(output.get("mentions", [])),
                        "relationship_candidate_count": len(output.get("relationships", [])),
                        "potential_discrepancy_count": len(output.get("potential_value_discrepancies", [])),
                    },
                )

        cancelled = await runs.is_cancel_requested(run_id, case_id, tenant_id)
        now = datetime.now(timezone.utc)
        has_extraction = any(spec.task_type.value == "extract_candidates" for spec in specs)
        has_graph_analysis = any(spec.task_type.value == "analyze_graph_patterns" for spec in specs)
        has_hypotheses = any(spec.task_type.value == "suggest_hypotheses" for spec in specs)
        stage = "candidate_analysis" if has_extraction else ("retrieval_and_graph_summary" if has_graph_analysis else "retrieval_only")
        mention_count = sum(len(value.get("mentions", [])) for value in completed_outputs.values())
        relationship_candidate_count = sum(
            len(value.get("relationships", [])) for value in completed_outputs.values()
        )
        potential_discrepancy_count = sum(
            len(value.get("potential_value_discrepancies", [])) for value in completed_outputs.values()
        )
        hypothesis_count = sum(len(value.get("hypotheses", [])) for value in completed_outputs.values())
        if cancelled:
            await runs.mark_queued_tasks_cancelled(run_id, case_id, tenant_id, now)
            final_status = RunStatus.CANCELLED
            summary = {"stage": stage, "completed_task_count": len(completed_ids)}
        elif failed:
            final_status = RunStatus.FAILED
            summary = {"stage": stage, "completed_task_count": len(completed_ids), "error_code": "task_failed"}
        else:
            final_status = RunStatus.COMPLETED_WITH_WARNINGS
            warnings = ["unverified_candidates"] if has_extraction else ["retrieval_only"]
            if has_graph_analysis:
                warnings.append("graph_summary_only")
            if has_hypotheses:
                warnings.append("unverified_hypotheses")
            if citation_count == 0:
                warnings.append("no_sources_found")
            summary = {
                "stage": stage,
                "completed_task_count": len(completed_ids),
                "citation_count": citation_count,
                "candidate_mention_count": mention_count,
                "relationship_candidate_count": relationship_candidate_count,
                "potential_discrepancy_count": potential_discrepancy_count,
                "hypothesis_count": hypothesis_count,
                "warnings": warnings,
                "limitations": [
                    "Candidates are unverified and are not written to the evidence graph.",
                    "Authorized human review and report generation are not part of this run phase.",
                ],
            }
        finished = await runs.finish_run(
            run_id, case_id, tenant_id, status=final_status.value, now=now, result_summary=summary
        )
        if finished is None:
            return
        final_status = RunStatus(finished["status"])
        if final_status == RunStatus.CANCELLED:
            await runs.mark_queued_tasks_cancelled(run_id, case_id, tenant_id, now)
        await events.publish(
            run_id=run_id, case_id=case_id, tenant_id=tenant_id,
            event_type="run.finished", payload={"status": final_status.value},
        )
    except Exception as exc:
        logger.error("Analysis run failed: run_id=%s error_class=%s", run_id, type(exc).__name__)
        now = datetime.now(timezone.utc)
        finished = await runs.finish_run(
            run_id, case_id, tenant_id, status=RunStatus.FAILED.value, now=now,
            result_summary={"error_code": "orchestration_failed"},
        )
        if finished is None:
            return
        try:
            event_type = "run.cancelled" if finished and finished["status"] == RunStatus.CANCELLED.value else "run.failed"
            await events.publish(
                run_id=run_id, case_id=case_id, tenant_id=tenant_id,
                event_type=event_type,
                payload={"status": finished["status"] if finished else RunStatus.FAILED.value, "error_code": "orchestration_failed"},
            )
        except Exception:
            pass
    finally:
        heartbeat.cancel()
        await asyncio.gather(heartbeat, return_exceptions=True)
        current = asyncio.current_task()
        if current is None or not current.cancelling():
            await runs.release_worker_lease(run_id, worker_id)


async def _execute_with_retries(spec: TaskSpec, context: TaskContext, settings: Settings) -> tuple[dict, int]:
    attempts_limit = min(spec.retry_limit, settings.max_retries_per_task) + 1
    last_error: Exception | None = None
    for attempt in range(1, attempts_limit + 1):
        try:
            output = await asyncio.wait_for(
                task_registry.execute(spec, context),
                timeout=min(spec.timeout_seconds, settings.max_task_timeout_seconds),
            )
            return output, attempt
        except Exception as exc:
            last_error = exc
            if attempt < attempts_limit:
                await asyncio.sleep(min(2 ** (attempt - 1), 5))
    assert last_error is not None
    raise TaskAttemptError(last_error, attempts_limit) from last_error


async def _renew_lease(runs: RunsRepository, run_id: str, worker_id: str, lease_seconds: int) -> None:
    interval = max(5, lease_seconds // 3)
    while True:
        await asyncio.sleep(interval)
        now = datetime.now(timezone.utc)
        renewed = await runs.renew_worker_lease(
            run_id, worker_id, now, datetime.fromtimestamp(now.timestamp() + lease_seconds, timezone.utc)
        )
        if not renewed:
            return


async def analysis_worker_loop(database: AsyncDatabase, qdrant, settings: Settings) -> None:
    """Poll Mongo's durable run queue and reclaim expired worker leases."""
    worker_id = f"worker_{uuid4().hex}"
    repository = RunsRepository(database)
    while True:
        now = datetime.now(timezone.utc)
        try:
            claimed = await repository.claim_next_run(
                worker_id,
                now,
                datetime.fromtimestamp(now.timestamp() + settings.worker_lease_seconds, timezone.utc),
            )
            if claimed is None:
                await asyncio.sleep(settings.worker_poll_interval_seconds)
                continue
            await execute_analysis_run(
                database,
                qdrant,
                settings,
                claimed["run_id"],
                claimed["case_id"],
                claimed["tenant_id"],
                worker_id,
            )
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.warning("Analysis queue poll failed: error_class=%s", type(exc).__name__)
            await asyncio.sleep(settings.worker_poll_interval_seconds)
