from pymongo.asynchronous.database import AsyncDatabase


class RelationshipsRepository:
    def __init__(self, database: AsyncDatabase):
        self.collection = database.relationships

    async def create(self, record: dict) -> None:
        await self.collection.insert_one(record)

    async def remove(self, case_id: str, relationship_id: str) -> None:
        await self.collection.delete_one({"case_id": case_id, "relationship_id": relationship_id})

    async def get_for_case(self, relationship_id: str, case_id: str, tenant_id: str) -> dict | None:
        return await self.collection.find_one(
            {"relationship_id": relationship_id, "case_id": case_id, "tenant_id": tenant_id}
        )

    async def list_for_case(self, case_id: str, tenant_id: str) -> list[dict]:
        cursor = self.collection.find({"case_id": case_id, "tenant_id": tenant_id}).sort("created_at", 1)
        return await cursor.to_list(length=10000)

    async def set_verification(
        self,
        relationship_id: str,
        case_id: str,
        tenant_id: str,
        *,
        decision: str,
        rationale: str,
        updated_at,
    ) -> dict | None:
        return await self.collection.find_one_and_update(
            {"relationship_id": relationship_id, "case_id": case_id, "tenant_id": tenant_id},
            {
                "$set": {
                    "verification_status": decision,
                    "verification_rationale": rationale,
                    "updated_at": updated_at,
                }
            },
            return_document=True,
        )

    async def set_review(
        self,
        relationship_id: str,
        case_id: str,
        tenant_id: str,
        *,
        decision: str,
        rationale: str,
        updated_at,
    ) -> dict | None:
        return await self.collection.find_one_and_update(
            {"relationship_id": relationship_id, "case_id": case_id, "tenant_id": tenant_id},
            {
                "$set": {
                    "review_status": decision,
                    "review_rationale": rationale,
                    "updated_at": updated_at,
                }
            },
            return_document=True,
        )
