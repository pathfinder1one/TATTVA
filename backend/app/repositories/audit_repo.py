from pymongo.asynchronous.database import AsyncDatabase


class AuditRepository:
    def __init__(self, database: AsyncDatabase):
        self.collection = database.audit_events

    async def append(self, event: dict) -> None:
        await self.collection.insert_one(event)
