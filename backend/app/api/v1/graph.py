from fastapi import APIRouter, Depends
from pymongo.asynchronous.database import AsyncDatabase

from app.dependencies import Actor, get_actor, get_database
from app.repositories.entities_repo import EntitiesRepository
from app.repositories.relationships_repo import RelationshipsRepository
from app.schemas.responses import CaseGraphResponse, EntityResponse, RelationshipResponse
from app.services.case_access import require_case_access
from app.services.anomaly_service import detect_graph_integrity_flags
from app.services.graph_service import build_case_graph

router = APIRouter(prefix="/cases/{case_id}/graph", tags=["graph"])


@router.get("", response_model=CaseGraphResponse)
async def get_case_graph(
    case_id: str,
    actor: Actor = Depends(get_actor),
    database: AsyncDatabase = Depends(get_database),
):
    await require_case_access(database, actor, case_id)
    entity_repo = EntitiesRepository(database)
    entities = await entity_repo.list_for_case(case_id, actor.tenant_id)
    mentions = await entity_repo.list_mentions(case_id, actor.tenant_id)
    relationships = await RelationshipsRepository(database).list_for_case(case_id, actor.tenant_id)
    graph = build_case_graph(entities, relationships, mentions)
    return CaseGraphResponse(
        case_id=case_id,
        entities=[EntityResponse(**entity) for entity in graph["entities"]],
        relationships=[RelationshipResponse(**relationship) for relationship in graph["relationships"]],
        metrics=graph["metrics"],
        metrics_note=graph["metrics_note"],
        syndicate_intelligence=graph.get("syndicate_intelligence"),
        integrity_flags=[
            flag.model_dump(mode="json")
            for flag in detect_graph_integrity_flags(
                {entity["entity_id"] for entity in entities}, relationships
            )
        ],
    )
