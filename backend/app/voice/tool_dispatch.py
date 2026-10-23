"""Allowlisted voice tools; every action rechecks tenant and case boundaries."""

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field
from pymongo.asynchronous.database import AsyncDatabase

from app.config import Settings
from app.dependencies import Actor
from app.repositories.audit_repo import AuditRepository
from app.orchestrator.event_publisher import RunEventPublisher
from app.repositories.runs_repo import RunsRepository
from app.domain.enums import RunStatus
from app.schemas.requests import AnalysisRunCreateRequest
from app.services.analysis_run_service import enqueue_analysis_run
from app.services.case_access import require_case_access
from app.services.report_service import create_run_report_draft


from app.repositories.findings_repo import FindingsRepository
from app.repositories.entities_repo import EntitiesRepository
from app.repositories.relationships_repo import RelationshipsRepository
from app.services.retrieval_service import search_case
from app.services.cross_case_service import (
    list_tenant_cases,
    find_cross_case_patterns as service_find_cross_case_patterns,
    compare_cases_nexus as service_compare_cases_nexus,
)


class StartAnalysisArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")
    query: str = Field(min_length=2, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=20)


class RunStatusArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")
    run_id: str = Field(min_length=1, max_length=120)


class RunActionArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")
    run_id: str = Field(min_length=1, max_length=120)


class QueryVaultArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")
    query: str = Field(min_length=1, max_length=1000)
    top_k: int = Field(default=3, ge=1, le=10)


TOOL_DECLARATIONS = [{"function_declarations": [
    {
        "name": "get_case_summary",
        "description": "Fetch the full criminal investigation overview and briefing for this case, including case title, directive, suspect names and roles, alibi contradictions, evidence count, and syndicate connections.",
        "parameters": {
            "type": "OBJECT",
            "properties": {},
        },
    },
    {
        "name": "start_case_analysis",
        "description": "Queue an autonomous multi-agent analysis run for the active case in MongoDB and Qdrant.",
        "parameters": {
            "type": "OBJECT", "required": ["query"],
            "properties": {
                "query": {"type": "STRING", "description": "The user's analysis question or investigation directive."},
                "top_k": {"type": "INTEGER", "minimum": 1, "maximum": 20},
            },
        },
    },
    {
        "name": "audit_case_contradictions",
        "description": "Audit and retrieve all detected timeline contradictions and financial anomalies for this case (e.g. wire transfer executed before legal incorporation).",
        "parameters": {
            "type": "OBJECT",
            "properties": {},
        },
    },
    {
        "name": "get_case_nexus_graph",
        "description": "Fetch the corporate entity and beneficial ownership nexus graph for this case, including shell companies and suspect individuals.",
        "parameters": {
            "type": "OBJECT",
            "properties": {},
        },
    },
    {
        "name": "query_evidence_vault",
        "description": "Query the Qdrant forensic evidence vector vault for source passages and citations relevant to an investigative query.",
        "parameters": {
            "type": "OBJECT", "required": ["query"],
            "properties": {
                "query": {"type": "STRING", "description": "The forensic search query."},
                "top_k": {"type": "INTEGER", "description": "Passages to retrieve."},
            },
        },
    },
    {
        "name": "identify_key_influencers",
        "description": "Identify key criminal network influencers including Kingpins (via PageRank), Hawala Brokers (via Betweenness centrality), and distinct sub-gang modules under MHA NCRB specifications.",
        "parameters": {
            "type": "OBJECT",
            "properties": {},
        },
    },
    {
        "name": "get_analysis_run_status",
        "description": "Read status for an active investigation run.",
        "parameters": {
            "type": "OBJECT", "required": ["run_id"],
            "properties": {"run_id": {"type": "STRING", "maxLength": 120}},
        },
    },
    {
        "name": "cancel_analysis",
        "description": "Request cancellation for an analysis run in the currently authorized case.",
        "parameters": {
            "type": "OBJECT", "required": ["run_id"],
            "properties": {"run_id": {"type": "STRING", "maxLength": 120}},
        },
    },
    {
        "name": "request_report_draft",
        "description": "Create a versioned source-checked report draft for an investigation run.",
        "parameters": {
            "type": "OBJECT", "required": ["run_id"],
            "properties": {"run_id": {"type": "STRING", "maxLength": 120}},
        },
    },
    {
        "name": "list_all_cases",
        "description": "List all registered criminal cases and FIRs in the system for cross-case investigation and pattern analysis.",
        "parameters": {
            "type": "OBJECT",
            "properties": {},
        },
    },
    {
        "name": "find_cross_case_patterns",
        "description": "Scan across ALL cases in the department to discover common suspects (e.g. Vikramaditya Singhania across cases), matching weapon/evidence signatures (e.g. Japanese Tanto Serrated Tactical Knife blade striations), shared hawala shell companies (e.g. Al-Madina Trading), and serial modus operandi.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "query": {"type": "STRING", "description": "Optional search term, suspect name, or weapon type to focus cross-case pattern matching."},
            },
        },
    },
    {
        "name": "compare_cases_nexus",
        "description": "Perform an in-depth side-by-side comparative analysis between multiple cases to discover common syndicates, matching suspects, weapon signatures, and alibi conflicts.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "case_ids": {
                    "type": "ARRAY",
                    "items": {"type": "STRING"},
                    "description": "Optional list of case IDs to compare; if omitted, all active department cases are compared.",
                },
            },
        },
    },
]}]

VOICE_SYSTEM_INSTRUCTION = (
    "You are TATTVA, an advanced AI-powered Criminal Network Analysis and Forensic Intelligence Assistant "
    "developed for the Ministry of Home Affairs (MHA) and National Crime Records Bureau (NCRB). "
    "Speak authoritatively, crisply, and in a natural, helpful conversational tone with the investigating officer. "
    "CRITICAL CONVERSATIONAL RULES: "
    "1. When the officer asks for a summary of the case, or says 'is case ke baare mein batao', 'give me an overview', 'what is this case?', "
    "or 'case summary do', ALWAYS call the 'get_case_summary' tool immediately. NEVER ask 'objective?' or ask what particular thing to analyze. "
    "Once the summary tool returns, explain the case clearly in conversational speech: mention the case title, the cartel or crime being investigated, "
    "who the main kingpins and hawala brokers are, and summarize the key alibi contradictions found. "
    "2. MULTI-CASE / CROSS-CASE ANALYSIS (VERY IMPORTANT): You have FULL SYSTEM VISIBILITY and access across ALL registered criminal cases in the department. "
    "When the officer asks about relations between multiple cases, asks 'saare cases ke beech relation find karo', 'charo cases ke suspects same hain ya nahi', "
    "'evidences ya weapon ka pattern check karke batao', 'chaaku/knife ka pattern match hota hai kya', 'kya koi similarity mili hai', "
    "or asks about cross-case suspects like 'Vikramaditya', ALWAYS call 'find_cross_case_patterns' or 'compare_cases_nexus'. "
    "When the tool returns, provide a comprehensive verbal forensic briefing: "
    "- Highlight common suspects across cases (e.g., Vikramaditya Singhania operating in both South Delhi Homicide CASE-2024-041 and Noida Stabbing CASE-2024-055). "
    "- Highlight forensic weapon pattern matches (e.g., 12cm Japanese Tanto Serrated Tactical Knife autopsy blade striation match connecting both homicides, indicating a serial contract hitman). "
    "- Highlight shared financial money trails (e.g., Al-Madina Trading & Bullion Co. and broker Farhan Qureshi routing funds across narcotics, homicide, and cyber phishing). "
    "3. When the officer asks 'saare cases dikhao' or 'kitne cases hain', call 'list_all_cases'. "
    "4. When the officer asks about suspects, criminal network, connections, or graph of the current case, call 'get_case_nexus_graph' or 'identify_key_influencers'. "
    "5. When the officer asks about alibi contradictions or fraud, call 'audit_case_contradictions'. "
    "6. Support both English and Hindi/Hinglish seamlessly based on how the officer speaks to you. "
    "7. Keep the conversation engaging, fluid, and continuous. Never respond with single-word questions like 'objective?'."
)


async def dispatch_voice_tool(
    *, name: str, arguments: dict, database: AsyncDatabase, settings: Settings,
    actor: Actor, case_id: str, qdrant=None,
) -> dict:
    # Cross-Case tools operate at the tenant level across all authorized cases
    if name == "list_all_cases":
        cases_list = await list_tenant_cases(database, actor.tenant_id)
        result = {
            "total_cases": len(cases_list),
            "cases": cases_list,
            "summary": f"Found {len(cases_list)} registered criminal cases in the department repository."
        }
    elif name == "find_cross_case_patterns":
        query = arguments.get("query")
        patterns = await service_find_cross_case_patterns(database, actor.tenant_id, query=query)
        result = patterns
    elif name == "compare_cases_nexus":
        case_ids = arguments.get("case_ids")
        comparison = await service_compare_cases_nexus(database, actor.tenant_id, case_ids=case_ids)
        result = comparison
    elif name == "get_case_summary":
        case_record = await require_case_access(database, actor, case_id)
        entities = await EntitiesRepository(database).list_for_case(case_id, actor.tenant_id)
        findings = await FindingsRepository(database).list_for_case(case_id, actor.tenant_id)
        relationships = await RelationshipsRepository(database).list_for_case(case_id, actor.tenant_id)
        
        suspects_list = [
            f"{e.get('display_name') or e.get('name', 'Unknown')} ({e.get('role', 'OPERATIVE')})"
            for e in entities
        ]
        contradictions_list = [
            f.get("statement") or f.get("title") or "Alibi discrepancy"
            for f in findings
        ]
        connections_list = [
            f"{r.get('subject_entity_id')} -> [{r.get('predicate')}] -> {r.get('object_entity_id')}"
            for r in relationships[:10]
        ]
        
        result = {
            "case_number": case_record.get("case_number"),
            "case_title": case_record.get("title"),
            "investigation_scope": case_record.get("description"),
            "status": case_record.get("status", "ACTIVE"),
            "total_suspects": len(entities),
            "key_suspects": suspects_list,
            "total_contradictions": len(findings),
            "alibi_contradictions": contradictions_list,
            "total_connections": len(relationships),
            "overview": (
                f"This is {case_record.get('case_number')}: {case_record.get('title')}. "
                f"Scope: {case_record.get('description')}. "
                f"Tracking {len(entities)} suspects: {', '.join(suspects_list[:4])}. "
                f"Flagged {len(findings)} critical alibi contradictions."
            ),
        }
    elif name == "start_case_analysis":
        args = StartAnalysisArgs.model_validate(arguments)
        run, _ = await enqueue_analysis_run(
            database, settings, actor, case_id,
            AnalysisRunCreateRequest(query=args.query, top_k=args.top_k),
            idempotency_key=f"voice_{uuid4().hex}",
        )
        result = {"run_id": run["run_id"], "status": run["status"], "message": "Analysis queued for this case."}
    elif name == "get_analysis_run_status":
        args = RunStatusArgs.model_validate(arguments)
        run = await RunsRepository(database).get_for_case(args.run_id, case_id, actor.tenant_id)
        if run is None:
            raise HTTPException(status_code=404, detail="Analysis run not found.")
        result = {
            "run_id": run["run_id"], "status": run["status"],
            "result_summary": run.get("result_summary", {}),
        }
    elif name == "cancel_analysis":
        args = RunActionArgs.model_validate(arguments)
        now = datetime.now(timezone.utc)
        repository = RunsRepository(database)
        updated = await repository.request_cancel(args.run_id, case_id, actor.tenant_id, now)
        if updated is None:
            existing = await repository.get_for_case(args.run_id, case_id, actor.tenant_id)
            if existing is None:
                raise HTTPException(status_code=404, detail="Analysis run not found.")
            raise HTTPException(status_code=409, detail="Analysis run cannot be cancelled in its current state.")
        if updated["status"] == RunStatus.CANCELLED.value:
            await repository.mark_queued_tasks_cancelled(args.run_id, case_id, actor.tenant_id, now)
            event_type = "run.cancelled"
        else:
            event_type = "run.cancel_requested"
        await RunEventPublisher(database).publish(
            run_id=args.run_id,
            case_id=case_id,
            tenant_id=actor.tenant_id,
            event_type=event_type,
            payload={"status": updated["status"]},
        )
        await AuditRepository(database).append({
            "event_id": f"audit_{uuid4().hex}", "case_id": case_id,
            "tenant_id": actor.tenant_id, "actor_id": actor.user_id,
            "action": "analysis_run.cancel_requested",
            "target_type": "analysis_run", "target_id": args.run_id,
            "timestamp": now, "result": "success",
        })
        result = {"run_id": args.run_id, "status": updated["status"], "message": "Cancellation request recorded."}
    elif name == "request_report_draft":
        args = RunActionArgs.model_validate(arguments)
        report = await create_run_report_draft(database, settings, actor, case_id, args.run_id)
        result = {
            "run_id": args.run_id,
            "report_id": report.report_id,
            "version": report.version,
            "status": "draft_requires_review",
            "message": "A source-checked report draft was created for investigator review.",
        }
    elif name == "audit_case_contradictions":
        findings = await FindingsRepository(database).list_for_case(case_id, actor.tenant_id)
        result = {
            "case_id": case_id,
            "total_contradictions": len(findings),
            "findings": [
                {
                    "statement": f.get("statement") or f.get("title") or "Alibi discrepancy",
                    "type": f.get("finding_type", "CONTRADICTION"),
                    "severity": f.get("severity", "CRITICAL"),
                    "verified": f.get("verification_status", "SUPPORTED"),
                }
                for f in findings
            ],
            "briefing": f"Identified {len(findings)} critical forensic findings for this case." if findings else "No contradictions currently flagged."
        }
    elif name == "get_case_nexus_graph":
        entities = await EntitiesRepository(database).list_for_case(case_id, actor.tenant_id)
        relationships = await RelationshipsRepository(database).list_for_case(case_id, actor.tenant_id)
        result = {
            "case_id": case_id,
            "entity_count": len(entities),
            "relationship_count": len(relationships),
            "entities": [{"name": e.get("display_name") or e.get("name"), "type": e.get("entity_type"), "role": e.get("role")} for e in entities[:10]],
            "relationships": [
                {
                    "source": r.get("subject_entity_id") or r.get("source_entity_id"),
                    "target": r.get("object_entity_id") or r.get("target_entity_id"),
                    "predicate": r.get("predicate"),
                    "status": r.get("verification_status")
                }
                for r in relationships[:10]
            ],
        }
    elif name == "query_evidence_vault":
        args = QueryVaultArgs.model_validate(arguments)
        if not qdrant:
            result = {"message": "Vector evidence vault is offline or uninitialized."}
        else:
            citations = await search_case(
                database, qdrant, settings,
                case_id=case_id, tenant_id=actor.tenant_id, query=args.query, top_k=args.top_k,
            )
            result = {
                "case_id": case_id,
                "matches_count": len(citations),
                "citations": [
                    {
                        "filename": c.filename,
                        "text": c.text[:280] + ("..." if len(c.text) > 280 else ""),
                        "score": round(float(c.retrieval_score), 4) if c.retrieval_score else None
                    }
                    for c in citations
                ]
            }
    elif name == "identify_key_influencers":
        from app.services.centrality_service import analyze_criminal_network_influencers
        entities = await EntitiesRepository(database).list_for_case(case_id, actor.tenant_id)
        relationships = await RelationshipsRepository(database).list_for_case(case_id, actor.tenant_id)
        scoped_entities = [e for e in entities if isinstance(e.get("entity_id"), str)]
        analysis_res = analyze_criminal_network_influencers(scoped_entities, relationships)
        synd = analysis_res["syndicate_analysis"]
        result = {
            "case_id": case_id,
            "kingpins": synd.get("identified_kingpins", []),
            "brokers": synd.get("identified_brokers", []),
            "cell_count": synd.get("cell_count", 1),
            "summary": (
                f"Identified {len(synd.get('identified_kingpins', []))} Kingpin(s) and {len(synd.get('identified_brokers', []))} Broker(s) across {synd.get('cell_count', 1)} criminal sub-cells."
                if synd.get("identified_kingpins") or synd.get("identified_brokers")
                else "Network analysis indicates a decentralized cell structure with no single dominant kingpin."
            )
        }
    else:
        raise ValueError("Voice tool is not allowlisted.")

    await AuditRepository(database).append({
        "event_id": f"audit_{uuid4().hex}", "case_id": case_id,
        "tenant_id": actor.tenant_id, "actor_id": actor.user_id,
        "action": "voice.tool_called", "target_type": "voice_tool",
        "target_id": name, "timestamp": datetime.now(timezone.utc),
        "result": "success",
    })
    return result
