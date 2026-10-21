from pymongo.asynchronous.database import AsyncDatabase


class EntitiesRepository:
    def __init__(self, database: AsyncDatabase):
        self.collection = database.entities
        self.mentions = database.entity_mentions

    async def create(self, record: dict) -> None:
        await self.collection.insert_one(record)

    async def add_mention(self, mention: dict) -> None:
        await self.mentions.insert_one(mention)

    async def remove(self, case_id: str, entity_id: str) -> None:
        await self.collection.delete_one({"case_id": case_id, "entity_id": entity_id})
        await self.mentions.delete_many({"case_id": case_id, "entity_id": entity_id})

    async def get_for_case(self, entity_id: str, case_id: str, tenant_id: str) -> dict | None:
        return await self.collection.find_one(
            {"entity_id": entity_id, "case_id": case_id, "tenant_id": tenant_id}
        )

    async def get_many(self, entity_ids: list[str], case_id: str, tenant_id: str) -> list[dict]:
        cursor = self.collection.find(
            {"entity_id": {"$in": entity_ids}, "case_id": case_id, "tenant_id": tenant_id}
        )
        return await cursor.to_list(length=100)

    async def list_for_case(self, case_id: str, tenant_id: str) -> list[dict]:
        cursor = self.collection.find({"case_id": case_id, "tenant_id": tenant_id}).sort("created_at", 1)
        return await cursor.to_list(length=5000)

    async def list_mentions(self, case_id: str, tenant_id: str) -> list[dict]:
        cursor = self.mentions.find({"case_id": case_id, "tenant_id": tenant_id}).sort("created_at", 1)
        return await cursor.to_list(length=10000)
