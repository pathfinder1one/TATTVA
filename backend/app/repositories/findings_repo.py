from pymongo import ReturnDocument
from pymongo.asynchronous.database import AsyncDatabase


class FindingsRepository:
    def __init__(self, database: AsyncDatabase):
        self.collection = database.findings

    async def create(self, record: dict) -> None:
        await self.collection.insert_one(record)

    async def remove(self, case_id: str, finding_id: str) -> None:
        await self.collection.delete_one({"case_id": case_id, "finding_id": finding_id})

    async def get_for_case(self, finding_id: str, case_id: str, tenant_id: str) -> dict | None:
        return await self.collection.find_one(
            {"finding_id": finding_id, "case_id": case_id, "tenant_id": tenant_id}
        )

    async def list_for_case(self, case_id: str, tenant_id: str, limit: int = 500) -> list[dict]:
        cursor = self.collection.find({"case_id": case_id, "tenant_id": tenant_id}).sort("created_at", -1)
        return await cursor.to_list(length=limit)

    async def set_review(
        self, finding_id: str, case_id: str, tenant_id: str, *, expected_status: str,
        decision: str, rationale: str, reviewer_id: str, updated_at
    ) -> dict | None:
        return await self.collection.find_one_and_update(
            {
                "finding_id": finding_id,
                "case_id": case_id,
                "tenant_id": tenant_id,
                "review_status": expected_status,
            },
            {"$set": {
                "review_status": decision,
                "review_rationale": rationale,
                "reviewed_by": reviewer_id,
                "updated_at": updated_at,
            }},
            return_document=ReturnDocument.AFTER,
        )
