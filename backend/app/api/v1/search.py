from fastapi import APIRouter, Depends, Request
from pymongo.asynchronous.database import AsyncDatabase

from app.config import Settings, get_settings
from app.dependencies import Actor, get_actor, get_database
from app.schemas.requests import CaseSearchRequest
from app.schemas.responses import CaseSearchResponse
from app.services.case_access import require_case_access
from app.services.retrieval_service import search_case

router = APIRouter(prefix="/cases/{case_id}/search", tags=["retrieval"])


@router.post("", response_model=CaseSearchResponse)
async def search_case_documents(
    case_id: str,
    request: Request,
    body: CaseSearchRequest,
    actor: Actor = Depends(get_actor),
    database: AsyncDatabase = Depends(get_database),
    settings: Settings = Depends(get_settings),
):
    await require_case_access(database, actor, case_id)
    citations = await search_case(
        database,
        request.app.state.qdrant,
        settings,
        case_id=case_id,
        tenant_id=actor.tenant_id,
        query=body.query,
        top_k=body.top_k,
    )
    request.app.state.qdrant_ready = True
    return CaseSearchResponse(
        case_id=case_id,
        query=body.query,
        citations=citations,
        limitations=[
            "Results are semantic retrieval matches, not verified relationships or findings.",
            "This endpoint returns source passages only; answer synthesis is not configured yet.",
        ],
    )
