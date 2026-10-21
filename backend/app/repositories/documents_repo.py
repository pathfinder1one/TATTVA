from pymongo.asynchronous.database import AsyncDatabase


class DocumentsRepository:
    def __init__(self, database: AsyncDatabase):
        self.collection = database.documents

    async def create(self, record: dict) -> None:
        await self.collection.insert_one(record)

    async def get_for_case(self, document_id: str, case_id: str, tenant_id: str) -> dict | None:
        return await self.collection.find_one(
            {"document_id": document_id, "case_id": case_id, "tenant_id": tenant_id}
        )

    async def mark_indexing(self, document_id: str, case_id: str, tenant_id: str) -> None:
        await self.collection.update_one(
            {"document_id": document_id, "case_id": case_id, "tenant_id": tenant_id},
            {"$set": {"status": "indexing"}},
        )

    async def mark_indexed(
        self, document_id: str, case_id: str, tenant_id: str, *, source_hash: str, parser_version: str, index_version: str
    ) -> None:
        await self.collection.update_one(
            {"document_id": document_id, "case_id": case_id, "tenant_id": tenant_id},
            {
                "$set": {
                    "status": "indexed",
                    "indexed_source_hash": source_hash,
                    "parser_version": parser_version,
                    "active_index_version": index_version,
                },
                "$unset": {"last_index_error": ""},
            },
        )

    async def record_indexing_failure(
        self, document_id: str, case_id: str, tenant_id: str, *, keep_previous_index: bool
    ) -> None:
        update = {"$set": {"last_index_error": "indexing_failed"}}
        if not keep_previous_index:
            update["$set"]["status"] = "indexing_failed"
        await self.collection.update_one(
            {"document_id": document_id, "case_id": case_id, "tenant_id": tenant_id}, update
        )

    async def list_for_case(self, case_id: str, tenant_id: str) -> list[dict]:
        cursor = self.collection.find({"case_id": case_id, "tenant_id": tenant_id}).sort("created_at", -1)
        return await cursor.to_list(length=500)
