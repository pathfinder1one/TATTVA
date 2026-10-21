from fastapi import Depends, Header, Request
from pymongo.asynchronous.database import AsyncDatabase

from app.api.v1.auth import resolve_actor
from app.config import Settings, get_settings
from app.core.identity import Actor


def get_database(request: Request) -> AsyncDatabase:
    return request.app.state.database


def get_actor(
    settings: Settings = Depends(get_settings),
    authorization: str | None = Header(default=None),
    x_user_id: str | None = Header(default=None),
    x_tenant_id: str | None = Header(default=None),
) -> Actor:
    return resolve_actor(
        settings,
        authorization=authorization,
        x_user_id=x_user_id,
        x_tenant_id=x_tenant_id,
    )
