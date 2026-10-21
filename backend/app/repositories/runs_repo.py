from datetime import datetime, timezone

from pymongo import ReturnDocument
from pymongo.asynchronous.database import AsyncDatabase


class RunsRepository:
    def __init__(self, database: AsyncDatabase):
        self.runs = database.analysis_runs
        self.tasks = database.tasks

    async def create(self, run: dict, tasks: list[dict]) -> None:
        if tasks:
            await self.tasks.insert_many(tasks, ordered=True)
        try:
            await self.runs.insert_one(run)
        except Exception:
            await self.tasks.delete_many({"run_id": run["run_id"]})
            raise

    async def activate_run(self, run_id: str, case_id: str, tenant_id: str, now) -> dict | None:
        return await self.runs.find_one_and_update(
            {"run_id": run_id, "case_id": case_id, "tenant_id": tenant_id, "status": "queued"},
            {"$set": {"queue_ready": True, "updated_at": now}},
            return_document=ReturnDocument.AFTER,
        )

    async def fail_unactivated_run(self, run_id: str, case_id: str, tenant_id: str, now) -> None:
        await self.runs.update_one(
            {
                "run_id": run_id,
                "case_id": case_id,
                "tenant_id": tenant_id,
                "status": "queued",
                "queue_ready": False,
            },
            {"$set": {
                "status": "failed",
                "result_summary": {"error_code": "run_enqueue_failed"},
                "updated_at": now,
            }},
        )
        await self.tasks.update_many(
            {"run_id": run_id, "case_id": case_id, "tenant_id": tenant_id, "status": "queued"},
            {"$set": {"status": "cancelled", "error_code": "run_enqueue_failed", "updated_at": now}},
        )

    async def get_for_case(self, run_id: str, case_id: str, tenant_id: str) -> dict | None:
        return await self.runs.find_one(
            {"run_id": run_id, "case_id": case_id, "tenant_id": tenant_id}
        )

    async def get_by_idempotency_key(
        self, key: str, case_id: str, tenant_id: str, actor_id: str
    ) -> dict | None:
        return await self.runs.find_one({
            "idempotency_key": key,
            "case_id": case_id,
            "tenant_id": tenant_id,
            "created_by": actor_id,
        })

    async def list_for_case(self, case_id: str, tenant_id: str, limit: int = 100) -> list[dict]:
        cursor = self.runs.find({"case_id": case_id, "tenant_id": tenant_id}).sort("created_at", -1)
        return await cursor.to_list(length=limit)

    async def list_tasks(self, run_id: str, case_id: str, tenant_id: str) -> list[dict]:
        cursor = self.tasks.find(
            {"run_id": run_id, "case_id": case_id, "tenant_id": tenant_id}
        ).sort("ordinal", 1)
        return await cursor.to_list(length=100)

    async def get_task(self, run_id: str, task_id: str, case_id: str, tenant_id: str) -> dict | None:
        return await self.tasks.find_one(
            {"run_id": run_id, "task_id": task_id, "case_id": case_id, "tenant_id": tenant_id}
        )

    async def update_task(self, run_id: str, task_id: str, case_id: str, tenant_id: str, updates: dict) -> None:
        await self.tasks.update_one(
            {"run_id": run_id, "task_id": task_id, "case_id": case_id, "tenant_id": tenant_id},
            {"$set": updates},
        )

    async def claim_next_run(self, worker_id: str, now, lease_expires_at) -> dict | None:
        return await self.runs.find_one_and_update(
            {
                "$or": [
                    {"status": "queued", "queue_ready": True},
                    {
                        "status": "queued",
                        "queue_ready": False,
                        "created_at": {"$lte": datetime.fromtimestamp(now.timestamp() - 30, timezone.utc)},
                    },
                    {"status": {"$in": ["running", "cancel_requested"]}, "lease_expires_at": {"$lte": now}},
                ]
            },
            [{"$set": {
                "status": {"$cond": [{"$eq": ["$status", "queued"]}, "running", "$status"]},
                "worker_id": worker_id,
                "lease_expires_at": lease_expires_at,
                "queue_ready": True,
                "updated_at": now,
            }}],
            sort=[("created_at", 1)],
            return_document=ReturnDocument.AFTER,
        )

    async def renew_worker_lease(self, run_id: str, worker_id: str, now, lease_expires_at) -> bool:
        result = await self.runs.update_one(
            {"run_id": run_id, "worker_id": worker_id, "status": {"$in": ["running", "cancel_requested"]}},
            {"$set": {"lease_expires_at": lease_expires_at, "updated_at": now}},
        )
        return result.modified_count == 1

    async def release_worker_lease(self, run_id: str, worker_id: str) -> None:
        await self.runs.update_one(
            {"run_id": run_id, "worker_id": worker_id},
            {"$unset": {"worker_id": "", "lease_expires_at": ""}},
        )

    async def finish_run(
        self,
        run_id: str,
        case_id: str,
        tenant_id: str,
        *,
        status: str,
        now,
        result_summary: dict,
    ) -> dict | None:
        return await self.runs.find_one_and_update(
            {
                "run_id": run_id,
                "case_id": case_id,
                "tenant_id": tenant_id,
                "status": {"$in": ["running", "cancel_requested"]},
            },
            [{"$set": {
                "status": {"$cond": [{"$eq": ["$status", "cancel_requested"]}, "cancelled", status]},
                "result_summary": result_summary,
                "updated_at": now,
            }}],
            return_document=ReturnDocument.AFTER,
        )

    async def request_cancel(self, run_id: str, case_id: str, tenant_id: str, now) -> dict | None:
        cancelled = await self.runs.find_one_and_update(
            {
                "run_id": run_id,
                "case_id": case_id,
                "tenant_id": tenant_id,
                "status": "queued",
            },
            {"$set": {"status": "cancelled", "updated_at": now}},
            return_document=ReturnDocument.AFTER,
        )
        if cancelled is not None:
            return cancelled
        return await self.runs.find_one_and_update(
            {
                "run_id": run_id,
                "case_id": case_id,
                "tenant_id": tenant_id,
                "status": "running",
            },
            {"$set": {"status": "cancel_requested", "updated_at": now}},
            return_document=ReturnDocument.AFTER,
        )

    async def mark_queued_tasks_cancelled(self, run_id: str, case_id: str, tenant_id: str, now) -> None:
        await self.tasks.update_many(
            {"run_id": run_id, "case_id": case_id, "tenant_id": tenant_id, "status": "queued"},
            {"$set": {"status": "cancelled", "updated_at": now}},
        )

    async def is_cancel_requested(self, run_id: str, case_id: str, tenant_id: str) -> bool:
        run = await self.runs.find_one(
            {"run_id": run_id, "case_id": case_id, "tenant_id": tenant_id},
            {"status": 1},
        )
        return bool(run and run.get("status") == "cancel_requested")
