from datetime import datetime, timezone
from uuid import uuid4

from fastapi import HTTPException
from pymongo.asynchronous.database import AsyncDatabase

from app.agents.report_builder import DraftReport, build_draft_report
from app.config import Settings
from app.dependencies import Actor
from app.repositories.audit_repo import AuditRepository
from app.repositories.evidence_repo import EvidenceRepository
from app.repositories.findings_repo import FindingsRepository
from app.repositories.runs_repo import RunsRepository
from app.repositories.reports_repo import ReportsRepository
from app.domain.enums import ReviewStatus
from app.services.evidence_validator import revalidate_evidence
from app.services.evidence_validator import resolve_source_span


async def create_run_report_draft(
    database: AsyncDatabase, settings: Settings, actor: Actor, case_id: str, run_id: str
) -> DraftReport:
    repository = RunsRepository(database)
    run = await repository.get_for_case(run_id, case_id, actor.tenant_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Analysis run not found.")
    if run.get("status") not in {"completed", "completed_with_warnings", "awaiting_review"}:
        raise HTTPException(status_code=409, detail="A report draft requires a completed analysis run.")
    tasks = await repository.list_tasks(run_id, case_id, actor.tenant_id)
    task_outputs = [
        task["output"] for task in tasks
        if task.get("status") == "completed" and isinstance(task.get("output"), dict)
    ]
    report = build_draft_report(
        run_id=run_id,
        case_id=case_id,
        query=run["query"],
        task_outputs=task_outputs,
    )
    current_citations = []
    valid_citation_ids = set()
    for citation in report.source_citations:
        try:
            chunk, document, quote = await resolve_source_span(
                database, settings, actor.tenant_id, case_id,
                citation["chunk_id"], citation["start_offset"], citation["end_offset"],
            )
        except HTTPException:
            report.limitations.append(
                f"Citation {citation.get('citation_id', 'unknown')} was omitted because its source no longer resolves."
            )
            continue
        if (
            chunk["document_id"] != citation["document_id"]
            or chunk["source_hash"] != citation["source_hash"]
            or chunk["parser_version"] != citation["parser_version"]
            or document["filename"] != citation["filename"]
            or quote != citation["text"]
        ):
            report.limitations.append(
                f"Citation {citation.get('citation_id', 'unknown')} was omitted because its source version changed."
            )
            continue
        current_citations.append(citation)
        valid_citation_ids.add(citation["citation_id"])
    report.source_citations = current_citations
    report.candidate_mentions = [
        item for item in report.candidate_mentions if item.get("citation_id") in valid_citation_ids
    ]
    report.candidate_relationships = [
        item for item in report.candidate_relationships if item.get("citation_id") in valid_citation_ids
    ]
    report.potential_value_discrepancies = [
        item for item in report.potential_value_discrepancies
        if all(claim.get("evidence_id") in valid_citation_ids for claim in item.get("claims", []))
    ]
    report.hypotheses = [
        item for item in report.hypotheses
        if all(
            reference.get("citation_id") in valid_citation_ids
            for side in ("evidence_for", "evidence_against")
            for reference in item.get(side, [])
        )
    ]
    accepted_findings = [
        finding for finding in await FindingsRepository(database).list_for_case(case_id, actor.tenant_id)
        if finding.get("review_status") == ReviewStatus.ACCEPTED_FOR_REPORT.value
    ]
    evidence_repo = EvidenceRepository(database)
    for finding in accepted_findings:
        evidence_records = await evidence_repo.get_many(
            finding.get("evidence_ids", []), case_id, actor.tenant_id
        )
        if len(evidence_records) != len(finding.get("evidence_ids", [])):
            report.limitations.append(f"Accepted finding {finding['finding_id']} was omitted because its evidence is incomplete.")
            continue
        evidence_is_valid = True
        for item in evidence_records:
            if not await revalidate_evidence(database, settings, item):
                evidence_is_valid = False
                break
        if not evidence_is_valid:
            report.limitations.append(f"Accepted finding {finding['finding_id']} was omitted because its source evidence no longer resolves.")
            continue
        report.reviewed_findings.append({
            "finding_id": finding["finding_id"],
            "finding_type": finding["finding_type"],
            "statement": finding["statement"],
            "review_status": finding["review_status"],
            "review_rationale": finding.get("review_rationale"),
            "reviewed_by": finding.get("reviewed_by"),
            "evidence": [
                {
                    "evidence_id": item["evidence_id"],
                    "document_id": item["document_id"],
                    "chunk_id": item["chunk_id"],
                    "source_hash": item["source_hash"],
                    "start_offset": item["start_offset"],
                    "end_offset": item["end_offset"],
                    "quote": item["quote"],
                }
                for item in evidence_records
            ],
        })
    if run.get("status") in {"failed", "cancelled", "cancel_requested"}:
        report.limitations.append(f"The analysis run ended with status: {run['status']}.")
    now = datetime.now(timezone.utc)
    report.report_id = f"report_{uuid4().hex}"
    report.created_at = now
    persisted = await ReportsRepository(database).create_version({
        "report_id": report.report_id,
        "case_id": case_id,
        "tenant_id": actor.tenant_id,
        "run_id": run_id,
        "version": 0,
        "report": report.model_dump(mode="json"),
        "created_by": actor.user_id,
        "created_at": now,
    })
    report.report_id = persisted["report_id"]
    report.version = persisted["version"]
    try:
        await AuditRepository(database).append(
            {
                "event_id": f"audit_{uuid4().hex}",
                "case_id": case_id,
                "tenant_id": actor.tenant_id,
                "actor_id": actor.user_id,
                "action": "report.draft_generated",
                "target_type": "analysis_run",
                "target_id": run_id,
                "timestamp": datetime.now(timezone.utc),
                "report_id": report.report_id,
                "version": report.version,
                "result": "success",
            }
        )
    except Exception:
        await ReportsRepository(database).remove(report.report_id, case_id, actor.tenant_id)
        raise
    return report
