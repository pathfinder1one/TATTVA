from pymongo.asynchronous.database import AsyncDatabase


class CasesRepository:
    def __init__(self, database: AsyncDatabase):
        self.collection = database.cases

    async def create(self, record: dict) -> None:
        await self.collection.insert_one(record)

    async def remove(self, case_id: str) -> None:
        await self.collection.delete_one({"case_id": case_id})

    async def get_for_tenant(self, case_id: str, tenant_id: str) -> dict | None:
        return await self.collection.find_one({"case_id": case_id, "tenant_id": tenant_id})

    async def list_for_member(self, tenant_id: str, user_id: str, memberships) -> list[dict]:
        member_case_ids = await memberships.collection.distinct(
            "case_id", {"tenant_id": tenant_id, "user_id": user_id}
        )
        cursor = self.collection.find(
            {"tenant_id": tenant_id, "case_id": {"$in": member_case_ids}}
        ).sort("created_at", -1)
        return await cursor.to_list(length=500)
