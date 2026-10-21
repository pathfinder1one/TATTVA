from datetime import datetime
from uuid import uuid4

from pymongo import ReturnDocument
from pymongo.asynchronous.database import AsyncDatabase


class RunEventsRepository:
    def __init__(self, database: AsyncDatabase):
        self.events = database.run_events
        self.runs = database.analysis_runs

    async def append(
        self, *, run_id: str, case_id: str, tenant_id: str, event_type: str, payload: dict, timestamp: datetime
    ) -> dict:
        run = await self.runs.find_one_and_update(
            {"run_id": run_id, "case_id": case_id, "tenant_id": tenant_id},
            {"$inc": {"event_seq": 1}, "$set": {"updated_at": timestamp}},
            projection={"event_seq": 1},
            return_document=ReturnDocument.AFTER,
        )
        if run is None:
            raise ValueError("Analysis run is unavailable for event recording.")
        event = {
            "event_id": f"event_{uuid4().hex}",
            "schema_version": 1,
            "run_id": run_id,
            "case_id": case_id,
            "tenant_id": tenant_id,
            "seq": run["event_seq"],
            "type": event_type,
            "timestamp": timestamp,
            "payload": payload,
        }
        await self.events.insert_one(event)
        return event

    async def list_after(
        self, *, run_id: str, case_id: str, tenant_id: str, after_seq: int, limit: int
    ) -> list[dict]:
        cursor = self.events.find(
            {"run_id": run_id, "case_id": case_id, "tenant_id": tenant_id, "seq": {"$gt": after_seq}}
        ).sort("seq", 1)
        return await cursor.to_list(length=limit)
