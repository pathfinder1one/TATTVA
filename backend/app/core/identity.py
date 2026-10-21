from dataclasses import dataclass


@dataclass(frozen=True)
class Actor:
    user_id: str
    tenant_id: str
