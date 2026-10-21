from fastapi import APIRouter, Depends
from pymongo.asynchronous.database import AsyncDatabase

from app.config import Settings, get_settings
from app.dependencies import Actor, get_actor, get_database
from app.repositories.relationships_repo import RelationshipsRepository
from app.schemas.requests import RelationshipCreateRequest, RelationshipReviewRequest, RelationshipVerificationRequest
from app.schemas.responses import RelationshipResponse
from app.services.case_access import require_case_access
from app.services.relationship_service import create_relationship, set_relationship_review, set_relationship_verification

router = APIRouter(prefix="/cases/{case_id}/relationships", tags=["relationships"])


@router.post("", response_model=RelationshipResponse, status_code=201)
async def post_relationship(
    case_id: str,
    body: RelationshipCreateRequest,
    actor: Actor = Depends(get_actor),
    database: AsyncDatabase = Depends(get_database),
    settings: Settings = Depends(get_settings),
):
    await require_case_access(database, actor, case_id)
    return await create_relationship(database, settings, actor, case_id, body)


@router.get("", response_model=list[RelationshipResponse])
async def list_relationships(
    case_id: str,
    actor: Actor = Depends(get_actor),
    database: AsyncDatabase = Depends(get_database),
):
    await require_case_access(database, actor, case_id)
    return await RelationshipsRepository(database).list_for_case(case_id, actor.tenant_id)


@router.post("/{relationship_id}/verify", response_model=RelationshipResponse)
async def verify_relationship(
    case_id: str,
    relationship_id: str,
    body: RelationshipVerificationRequest,
    actor: Actor = Depends(get_actor),
    database: AsyncDatabase = Depends(get_database),
    settings: Settings = Depends(get_settings),
):
    await require_case_access(database, actor, case_id)
    return await set_relationship_verification(
        database, settings, actor, case_id, relationship_id, body.decision, body.rationale
    )


@router.post("/{relationship_id}/review", response_model=RelationshipResponse)
async def review_relationship(
    case_id: str,
    relationship_id: str,
    body: RelationshipReviewRequest,
    actor: Actor = Depends(get_actor),
    database: AsyncDatabase = Depends(get_database),
):
    await require_case_access(database, actor, case_id)
    return await set_relationship_review(
        database, actor, case_id, relationship_id, body.decision, body.rationale
    )
