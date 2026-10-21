from fastapi import APIRouter, Depends
from pymongo.asynchronous.database import AsyncDatabase

from app.config import Settings, get_settings
from app.dependencies import Actor, get_actor, get_database
from app.repositories.findings_repo import FindingsRepository
from app.schemas.requests import FindingCreateRequest, FindingReviewRequest
from app.schemas.responses import FindingResponse
from app.services.case_access import require_case_access
from app.services.finding_service import create_finding_candidate, review_finding

router = APIRouter(prefix="/cases/{case_id}/findings", tags=["findings"])


@router.get("", response_model=list[FindingResponse])
async def list_findings(
    case_id: str,
    actor: Actor = Depends(get_actor),
    database: AsyncDatabase = Depends(get_database),
):
    await require_case_access(database, actor, case_id)
    return await FindingsRepository(database).list_for_case(case_id, actor.tenant_id)


@router.post("", response_model=FindingResponse, status_code=201)
async def post_finding(
    case_id: str,
    body: FindingCreateRequest,
    actor: Actor = Depends(get_actor),
    database: AsyncDatabase = Depends(get_database),
    settings: Settings = Depends(get_settings),
):
    await require_case_access(database, actor, case_id)
    return await create_finding_candidate(database, settings, actor, case_id, body)


@router.post("/{finding_id}/review", response_model=FindingResponse)
async def post_finding_review(
    case_id: str,
    finding_id: str,
    body: FindingReviewRequest,
    actor: Actor = Depends(get_actor),
    database: AsyncDatabase = Depends(get_database),
    settings: Settings = Depends(get_settings),
):
    await require_case_access(database, actor, case_id)
    return await review_finding(
        database, settings, actor, case_id, finding_id, body.decision, body.rationale
    )
