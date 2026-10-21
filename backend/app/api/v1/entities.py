from fastapi import APIRouter, Depends
from pymongo.asynchronous.database import AsyncDatabase

from app.config import Settings, get_settings
from app.dependencies import Actor, get_actor, get_database
from app.repositories.entities_repo import EntitiesRepository
from app.schemas.requests import EntityCreateRequest
from app.schemas.responses import EntityResponse
from app.services.case_access import require_case_access
from app.services.entity_service import create_entity

router = APIRouter(prefix="/cases/{case_id}/entities", tags=["entities"])


@router.post("", response_model=EntityResponse, status_code=201)
async def post_entity(
    case_id: str,
    body: EntityCreateRequest,
    actor: Actor = Depends(get_actor),
    database: AsyncDatabase = Depends(get_database),
    settings: Settings = Depends(get_settings),
):
    await require_case_access(database, actor, case_id)
    return await create_entity(database, settings, actor, case_id, body)


@router.get("", response_model=list[EntityResponse])
async def list_entities(
    case_id: str,
    actor: Actor = Depends(get_actor),
    database: AsyncDatabase = Depends(get_database),
):
    await require_case_access(database, actor, case_id)
    repo = EntitiesRepository(database)
    entities = await repo.list_for_case(case_id, actor.tenant_id)
    mentions = await repo.list_mentions(case_id, actor.tenant_id)
    evidence_by_entity: dict[str, list[str]] = {}
    for mention in mentions:
        evidence_by_entity.setdefault(mention["entity_id"], []).append(mention["evidence_id"])
    return [
        {**entity, "evidence_ids": evidence_by_entity.get(entity["entity_id"], [])}
        for entity in entities
    ]
