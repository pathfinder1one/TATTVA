import re
from datetime import datetime, timezone
from uuid import uuid4

from pymongo.asynchronous.database import AsyncDatabase

from app.dependencies import Actor
from app.domain.entity import EntityRecord
from app.repositories.audit_repo import AuditRepository
from app.repositories.entities_repo import EntitiesRepository
from app.repositories.evidence_repo import EvidenceRepository
from app.schemas.requests import EntityCreateRequest
from app.services.evidence_validator import create_evidence_records


async def create_entity(database: AsyncDatabase, settings, actor: Actor, case_id: str, request: EntityCreateRequest):
    now = datetime.now(timezone.utc)
    entity_id = f"entity_{uuid4().hex}"
    record = EntityRecord(
        entity_id=entity_id,
        case_id=case_id,
        tenant_id=actor.tenant_id,
        entity_type=request.entity_type,
        display_name=request.display_name,
        normalized_name=re.sub(r"\s+", " ", request.display_name).strip().casefold(),
        created_by=actor.user_id,
        created_at=now,
    )
    repo = EntitiesRepository(database)
    evidence_records = []
    try:
        await repo.create(record.to_document())
        evidence_records = await create_evidence_records(
            database, settings, actor, case_id, request.source_spans, "entity_mention"
        )
        for evidence in evidence_records:
            await repo.add_mention(
                {
                    "mention_id": f"mention_{uuid4().hex}",
                    "case_id": case_id,
                    "tenant_id": actor.tenant_id,
                    "entity_id": entity_id,
                    "evidence_id": evidence.evidence_id,
                    "document_id": evidence.document_id,
                    "chunk_id": evidence.chunk_id,
                    "source_hash": evidence.source_hash,
                    "start_offset": evidence.start_offset,
                    "end_offset": evidence.end_offset,
                    "created_by": actor.user_id,
                    "created_at": now,
                }
            )
        await AuditRepository(database).append(
            {
                "event_id": f"audit_{uuid4().hex}",
                "case_id": case_id,
                "tenant_id": actor.tenant_id,
                "actor_id": actor.user_id,
                "action": "entity.created",
                "target_type": "entity",
                "target_id": entity_id,
                "timestamp": now,
                "result": "success",
            }
        )
    except Exception:
        await repo.remove(case_id, entity_id)
        for evidence in evidence_records:
            await EvidenceRepository(database).remove(case_id, evidence.evidence_id)
        raise
    return {**record.model_dump(mode="python"), "evidence_ids": [e.evidence_id for e in evidence_records]}
