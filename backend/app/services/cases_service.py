from datetime import datetime, timezone
from uuid import uuid4

from pymongo.errors import DuplicateKeyError

from app.dependencies import Actor
from app.domain.case import CaseRecord
from app.repositories.cases_repo import CasesRepository
from app.repositories.memberships_repo import MembershipsRepository
from app.schemas.requests import CaseCreateRequest


async def create_case(database, actor: Actor, request: CaseCreateRequest) -> CaseRecord:
    now = datetime.now(timezone.utc)
    record = CaseRecord(
        case_id=f"case_{uuid4().hex}",
        tenant_id=actor.tenant_id,
        case_number=request.case_number,
        title=request.title,
        description=request.description,
        created_by=actor.user_id,
        created_at=now,
        updated_at=now,
    )
    cases = CasesRepository(database)
    memberships = MembershipsRepository(database)
    try:
        await cases.create(record.to_document())
        await memberships.add_owner(
            case_id=record.case_id, tenant_id=actor.tenant_id, user_id=actor.user_id, created_at=now
        )
    except DuplicateKeyError as exc:
        from fastapi import HTTPException

        raise HTTPException(status_code=409, detail="A case with this number already exists in this tenant.") from exc
    except Exception:
        await cases.remove(record.case_id)
        await memberships.remove(case_id=record.case_id, user_id=actor.user_id)
        raise
    return record
