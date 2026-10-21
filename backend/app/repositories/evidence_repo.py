from pymongo.asynchronous.database import AsyncDatabase


class EvidenceRepository:
    def __init__(self, database: AsyncDatabase):
        self.collection = database.evidence

    async def create(self, record: dict) -> None:
        await self.collection.insert_one(record)

    async def remove(self, case_id: str, evidence_id: str) -> None:
        await self.collection.delete_one({"case_id": case_id, "evidence_id": evidence_id})

    async def get_for_case(self, evidence_id: str, case_id: str, tenant_id: str) -> dict | None:
        return await self.collection.find_one(
            {"evidence_id": evidence_id, "case_id": case_id, "tenant_id": tenant_id}
        )

    async def get_many(self, evidence_ids: list[str], case_id: str, tenant_id: str) -> list[dict]:
        cursor = self.collection.find(
            {"evidence_id": {"$in": evidence_ids}, "case_id": case_id, "tenant_id": tenant_id}
        )
        return await cursor.to_list(length=100)
