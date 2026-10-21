from pymongo.asynchronous.database import AsyncDatabase


class ChunksRepository:
    def __init__(self, database: AsyncDatabase):
        self.chunks = database.document_chunks
        self.versions = database.extracted_text_versions

    async def save_version(self, version: dict) -> None:
        await self.versions.update_one(
            {
                "document_id": version["document_id"],
                "source_hash": version["source_hash"],
                "parser_version": version["parser_version"],
            },
            {"$setOnInsert": version},
            upsert=True,
        )

    async def get_version(self, document_id: str, source_hash: str, parser_version: str) -> dict | None:
        return await self.versions.find_one(
            {"document_id": document_id, "source_hash": source_hash, "parser_version": parser_version}
        )

    async def get_version_for_index(
        self, document_id: str, source_hash: str, parser_version: str, index_version: str
    ) -> dict | None:
        return await self.versions.find_one(
            {
                "document_id": document_id,
                "source_hash": source_hash,
                "parser_version": parser_version,
                "index_version": index_version,
            }
        )

    async def save_chunks(self, chunks: list[dict]) -> None:
        for chunk in chunks:
            await self.chunks.update_one(
                {"chunk_id": chunk["chunk_id"]}, {"$setOnInsert": chunk}, upsert=True
            )

    async def get_chunk(self, chunk_id: str, case_id: str, tenant_id: str) -> dict | None:
        return await self.chunks.find_one(
            {"chunk_id": chunk_id, "case_id": case_id, "tenant_id": tenant_id}
        )

