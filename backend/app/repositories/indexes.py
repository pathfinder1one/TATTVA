from pymongo.asynchronous.database import AsyncDatabase


async def ensure_indexes(database: AsyncDatabase) -> None:
    await database.cases.create_index([("tenant_id", 1), ("case_number", 1)], unique=True)
    await database.case_memberships.create_index([("case_id", 1), ("user_id", 1)], unique=True)
    await database.case_memberships.create_index([("tenant_id", 1), ("user_id", 1)])
    await database.documents.create_index([("case_id", 1), ("created_at", -1)])
    await database.documents.create_index([("case_id", 1), ("sha256", 1)])
    await database.entities.create_index([("case_id", 1), ("entity_id", 1)], unique=True)
    await database.entities.create_index([("case_id", 1), ("entity_type", 1), ("normalized_name", 1)])
    await database.entity_mentions.create_index([("case_id", 1), ("entity_id", 1), ("created_at", -1)])
    await database.relationships.create_index([("case_id", 1), ("relationship_id", 1)], unique=True)
    await database.relationships.create_index([("case_id", 1), ("verification_status", 1)])
    await database.relationships.create_index([("case_id", 1), ("subject_entity_id", 1), ("object_entity_id", 1)])
    await database.findings.create_index([("tenant_id", 1), ("case_id", 1), ("created_at", -1)])
    await database.findings.create_index([("case_id", 1), ("review_status", 1)])
    await database.reports.create_index([("tenant_id", 1), ("case_id", 1), ("run_id", 1), ("version", -1)])
    await database.reports.create_index([("tenant_id", 1), ("case_id", 1), ("run_id", 1), ("version", 1)], unique=True)
    await database.reports.create_index([("report_id", 1)], unique=True)
    await database.evidence.create_index([("case_id", 1), ("evidence_id", 1)], unique=True)
    await database.evidence.create_index([("case_id", 1), ("chunk_id", 1)])
    await database.extracted_text_versions.create_index(
        [("document_id", 1), ("source_hash", 1), ("parser_version", 1)], unique=True
    )
    await database.document_chunks.create_index([("chunk_id", 1)], unique=True)
    await database.document_chunks.create_index([("case_id", 1), ("document_id", 1), ("index_version", 1)])
    await database.analysis_runs.create_index([("tenant_id", 1), ("case_id", 1), ("created_at", -1)])
    await database.analysis_runs.create_index(
        [("tenant_id", 1), ("case_id", 1), ("created_by", 1), ("idempotency_key", 1)],
        unique=True,
        partialFilterExpression={"idempotency_key": {"$type": "string"}},
    )
    await database.analysis_runs.create_index([("status", 1), ("updated_at", 1)])
    await database.tasks.create_index([("run_id", 1), ("status", 1)])
    await database.tasks.create_index([("tenant_id", 1), ("case_id", 1), ("run_id", 1), ("task_id", 1)], unique=True)
    await database.run_events.create_index([("run_id", 1), ("seq", 1)], unique=True)
    await database.run_events.create_index([("tenant_id", 1), ("case_id", 1), ("run_id", 1), ("seq", 1)])
    await database.audit_events.create_index([("case_id", 1), ("timestamp", -1)])
    await database.audit_events.create_index([("actor_id", 1), ("timestamp", -1)])
