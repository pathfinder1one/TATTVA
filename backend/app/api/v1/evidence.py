from fastapi import APIRouter, Depends, HTTPException
from pymongo.asynchronous.database import AsyncDatabase

from app.config import Settings, get_settings
from app.dependencies import Actor, get_actor, get_database
from app.repositories.evidence_repo import EvidenceRepository
from app.schemas.responses import EvidenceResponse
from app.services.case_access import require_case_access
from app.services.evidence_validator import revalidate_evidence

router = APIRouter(prefix="/cases/{case_id}/evidence", tags=["evidence"])


@router.get("/{evidence_id}", response_model=EvidenceResponse)
async def get_evidence(
    case_id: str,
    evidence_id: str,
    actor: Actor = Depends(get_actor),
    database: AsyncDatabase = Depends(get_database),
    settings: Settings = Depends(get_settings),
):
    await require_case_access(database, actor, case_id)
    evidence = await EvidenceRepository(database).get_for_case(evidence_id, case_id, actor.tenant_id)
    if evidence is None:
        raise HTTPException(status_code=404, detail="Evidence not found.")
    if not await revalidate_evidence(database, settings, evidence):
        raise HTTPException(status_code=409, detail="Evidence no longer resolves to its immutable source span.")
    return evidence
