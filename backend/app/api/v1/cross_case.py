from typing import Any
from fastapi import APIRouter, Depends
from pymongo.asynchronous.database import AsyncDatabase

from app.dependencies import Actor, get_actor, get_database
from app.services.cross_case_service import (
    list_tenant_cases,
    find_cross_case_patterns,
    compare_cases_nexus,
)

router = APIRouter(prefix="/cross-case", tags=["cross-case"])


@router.get("/cases")
async def get_all_cases(
    actor: Actor = Depends(get_actor),
    database: AsyncDatabase = Depends(get_database),
) -> dict[str, Any]:
    cases = await list_tenant_cases(database, actor.tenant_id)
    return {"total_cases": len(cases), "cases": cases}


@router.get("/patterns")
async def get_cross_case_patterns(
    query: str | None = None,
    actor: Actor = Depends(get_actor),
    database: AsyncDatabase = Depends(get_database),
) -> dict[str, Any]:
    return await find_cross_case_patterns(database, actor.tenant_id, query=query)


@router.post("/compare")
async def post_compare_cases(
    payload: dict[str, Any],
    actor: Actor = Depends(get_actor),
    database: AsyncDatabase = Depends(get_database),
) -> dict[str, Any]:
    case_ids = payload.get("case_ids")
    return await compare_cases_nexus(database, actor.tenant_id, case_ids=case_ids)
