from fastapi import HTTPException, status
from pymongo.asynchronous.database import AsyncDatabase

from app.dependencies import Actor
from app.repositories.cases_repo import CasesRepository
from app.repositories.memberships_repo import MembershipsRepository


async def require_case_access(database: AsyncDatabase, actor: Actor, case_id: str) -> dict:
    case = await CasesRepository(database).get_for_tenant(case_id, actor.tenant_id)
    member = await MembershipsRepository(database).can_access(
        case_id=case_id, tenant_id=actor.tenant_id, user_id=actor.user_id
    )
    if case is None or not member:
        # Conceal whether a case exists outside the caller's scope.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found.")
    return case
