from fastapi import APIRouter, Depends, status
from pymongo.asynchronous.database import AsyncDatabase

from app.dependencies import Actor, get_actor, get_database
from app.repositories.cases_repo import CasesRepository
from app.repositories.memberships_repo import MembershipsRepository
from app.schemas.requests import CaseCreateRequest
from app.schemas.responses import CaseResponse
from app.services.case_access import require_case_access
from app.services.cases_service import create_case

router = APIRouter(prefix="/cases", tags=["cases"])


@router.post("", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
async def post_case(
    body: CaseCreateRequest,
    actor: Actor = Depends(get_actor),
    database: AsyncDatabase = Depends(get_database),
):
    return await create_case(database, actor, body)


@router.get("", response_model=list[CaseResponse])
async def list_cases(actor: Actor = Depends(get_actor), database: AsyncDatabase = Depends(get_database)):
    return await CasesRepository(database).list_for_member(
        actor.tenant_id, actor.user_id, MembershipsRepository(database)
    )


@router.get("/{case_id}", response_model=CaseResponse)
async def get_case(
    case_id: str,
    actor: Actor = Depends(get_actor),
    database: AsyncDatabase = Depends(get_database),
):
    return await require_case_access(database, actor, case_id)
