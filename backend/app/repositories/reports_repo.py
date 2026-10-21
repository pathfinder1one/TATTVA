from pymongo.asynchronous.database import AsyncDatabase
from uuid import uuid4


class ReportsRepository:
    def __init__(self, database: AsyncDatabase):
        self.collection = database.reports

    async def next_version(self, case_id: str, tenant_id: str, run_id: str) -> int:
        row = await self.collection.find_one(
            {"case_id": case_id, "tenant_id": tenant_id, "run_id": run_id},
            {"version": 1}, sort=[("version", -1)],
        )
        return (row["version"] if row else 0) + 1

    async def create_version(self, record: dict) -> dict:
        # Concurrent drafts may choose the same next version. Retry the unique
        # case/run/version slot rather than returning an unpersisted draft.
        from pymongo.errors import DuplicateKeyError

        for _ in range(5):
            candidate = {key: value for key, value in record.items() if key != "_id"}
            candidate.setdefault("report_id", f"report_{uuid4().hex}")
            candidate["version"] = await self.next_version(
                candidate["case_id"], candidate["tenant_id"], candidate["run_id"]
            )
            candidate["report"]["report_id"] = candidate["report_id"]
            candidate["report"]["version"] = candidate["version"]
            try:
                await self.collection.insert_one(candidate)
                return candidate
            except DuplicateKeyError:
                continue
        raise RuntimeError("Could not allocate a report version after concurrent updates.")

    async def get_for_case(self, report_id: str, case_id: str, tenant_id: str) -> dict | None:
        return await self.collection.find_one(
            {"report_id": report_id, "case_id": case_id, "tenant_id": tenant_id}
        )

    async def remove(self, report_id: str, case_id: str, tenant_id: str) -> None:
        await self.collection.delete_one({
            "report_id": report_id, "case_id": case_id, "tenant_id": tenant_id,
        })

    async def list_for_run(self, case_id: str, tenant_id: str, run_id: str) -> list[dict]:
        cursor = self.collection.find(
            {"case_id": case_id, "tenant_id": tenant_id, "run_id": run_id}
        ).sort("version", -1)
        records = await cursor.to_list(length=50)
        return [{
            "report_id": item["report_id"], "run_id": item["run_id"],
            "version": item["version"], "created_by": item["created_by"],
            "created_at": item["created_at"], "report_type": item["report"].get("report_type"),
        } for item in records]
