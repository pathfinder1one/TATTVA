"""Versioned persisted event contract; live event delivery is a later phase."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class RunEvent(BaseModel):
    event_id: str
    schema_version: int = 1
    run_id: str
    seq: int
    type: str
    timestamp: datetime
    payload: dict[str, Any]
