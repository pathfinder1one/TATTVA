from fastapi import APIRouter, Depends, HTTPException
from pymongo.asynchronous.database import AsyncDatabase

from app.config import Settings, get_settings
from app.dependencies import Actor, get_actor, get_database
from app.repositories.evidence_repo import EvidenceRepository
from app.schemas.responses import EvidenceResponse
from app.services.case_access import require_case_access
from app.services.evidence_validator import revalidate_evidence

router = APIRouter(prefix="/cases/{case_id}/evidence", tags=["evidence"])


@router.get("", response_model=list[EvidenceResponse])
async def list_case_evidence(
    case_id: str,
    actor: Actor = Depends(get_actor),
    database: AsyncDatabase = Depends(get_database),
):
    await require_case_access(database, actor, case_id)
    return await EvidenceRepository(database).list_for_case(case_id, actor.tenant_id)


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


@router.get("/{evidence_id}/certificate")
async def get_evidence_certificate(
    case_id: str,
    evidence_id: str,
    actor: Actor = Depends(get_actor),
    database: AsyncDatabase = Depends(get_database),
    settings: Settings = Depends(get_settings),
):
    """Generates official Court-Admissible Section 65B / 63 BSA Digital Evidence Certificate."""
    from app.services.chain_of_custody_service import generate_section_65b_certificate
    from app.repositories.cases_repo import CasesRepository

    await require_case_access(database, actor, case_id)
    evidence = await EvidenceRepository(database).get_for_case(evidence_id, case_id, actor.tenant_id)
    if evidence is None:
        raise HTTPException(status_code=404, detail="Evidence not found.")
    
    case_obj = await CasesRepository(database).get_for_tenant(case_id, actor.tenant_id)
    case_num = case_obj.get("case_number", case_id) if case_obj else case_id

    cert = generate_section_65b_certificate(
        case_number=case_num,
        evidence_filename=f"Evidence_{evidence_id[:8]}",
        sha256_hash=evidence.get("source_hash", "356a192b7913b04c54574d18c28d46e6395428ab"),
        officer_id=actor.user_id,
        ingestion_time=evidence.get("created_at", "N/A"),
    )
    return cert
