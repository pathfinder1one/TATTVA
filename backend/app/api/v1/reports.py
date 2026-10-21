from fastapi import APIRouter, Depends, HTTPException
from pymongo.asynchronous.database import AsyncDatabase

from app.agents.report_builder import DraftReport
from app.config import Settings, get_settings
from app.dependencies import Actor, get_actor, get_database
from app.services.case_access import require_case_access
from app.services.report_service import create_run_report_draft
from app.repositories.reports_repo import ReportsRepository

router = APIRouter(prefix="/cases/{case_id}/analysis-runs", tags=["reports"])


@router.post("/{run_id}/report-draft", response_model=DraftReport)
async def generate_run_report_draft(
    case_id: str,
    run_id: str,
    actor: Actor = Depends(get_actor),
    database: AsyncDatabase = Depends(get_database),
    settings: Settings = Depends(get_settings),
):
    await require_case_access(database, actor, case_id)
    return await create_run_report_draft(database, settings, actor, case_id, run_id)


@router.get("/{run_id}/reports")
async def list_run_reports(
    case_id: str,
    run_id: str,
    actor: Actor = Depends(get_actor),
    database: AsyncDatabase = Depends(get_database),
):
    await require_case_access(database, actor, case_id)
    return await ReportsRepository(database).list_for_run(case_id, actor.tenant_id, run_id)


@router.get("/{run_id}/reports/{report_id}", response_model=DraftReport)
async def get_run_report(
    case_id: str,
    run_id: str,
    report_id: str,
    actor: Actor = Depends(get_actor),
    database: AsyncDatabase = Depends(get_database),
):
    await require_case_access(database, actor, case_id)
    record = await ReportsRepository(database).get_for_case(report_id, case_id, actor.tenant_id)
    if record is None or record.get("run_id") != run_id:
        raise HTTPException(status_code=404, detail="Report draft not found.")
    return record["report"]
