from datetime import datetime, timezone

from pymongo.asynchronous.database import AsyncDatabase

from app.repositories.events_repo import RunEventsRepository


class RunEventPublisher:
    """Persists ordered run events; subscriber transport can consume them later."""

    def __init__(self, database: AsyncDatabase):
        self.repository = RunEventsRepository(database)

    async def publish(
        self, *, run_id: str, case_id: str, tenant_id: str, event_type: str, payload: dict
    ) -> dict:
        return await self.repository.append(
            run_id=run_id,
            case_id=case_id,
            tenant_id=tenant_id,
            event_type=event_type,
            payload=payload,
            timestamp=datetime.now(timezone.utc),
        )
