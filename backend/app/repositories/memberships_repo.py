from pymongo.asynchronous.database import AsyncDatabase


class MembershipsRepository:
    def __init__(self, database: AsyncDatabase):
        self.collection = database.case_memberships

    async def add_owner(self, *, case_id: str, tenant_id: str, user_id: str, created_at) -> None:
        await self.collection.insert_one(
            {
                "case_id": case_id,
                "tenant_id": tenant_id,
                "user_id": user_id,
                "role": "owner",
                "created_at": created_at,
            }
        )

    async def can_access(self, *, case_id: str, tenant_id: str, user_id: str) -> bool:
        return await self.collection.find_one(
            {"case_id": case_id, "tenant_id": tenant_id, "user_id": user_id}
        ) is not None

    async def remove(self, *, case_id: str, user_id: str) -> None:
        await self.collection.delete_one({"case_id": case_id, "user_id": user_id})

    async def get_role(self, *, case_id: str, tenant_id: str, user_id: str) -> str | None:
        membership = await self.collection.find_one(
            {"case_id": case_id, "tenant_id": tenant_id, "user_id": user_id}, {"role": 1}
        )
        return membership.get("role") if membership else None
