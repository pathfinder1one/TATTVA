from collections import Counter
from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from app.domain.task_spec import TaskType
from app.orchestrator.task_registry import TaskContext, TaskDefinition, task_registry
from app.repositories.entities_repo import EntitiesRepository
from app.repositories.relationships_repo import RelationshipsRepository


class GraphPatternSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    entity_count: int = Field(ge=0)
    relationship_count: int = Field(ge=0)
    average_degree: float = Field(ge=0)
    directed_density: float = Field(ge=0, le=1)
    degree_counts: dict[str, int]
    note: str = "Structural measurements only; not evidence strength or a measure of wrongdoing."


def summarize_graph(entities: list[dict[str, Any]], relationships: list[dict[str, Any]]) -> GraphPatternSummary:
    """Compute transparent counts from recorded edges without ranking people."""
    entity_ids = {
        entity.get("entity_id") for entity in entities
        if isinstance(entity.get("entity_id"), str)
    }
    degrees: Counter[str] = Counter({entity_id: 0 for entity_id in entity_ids})
    valid_edges = 0
    unique_pairs: set[tuple[str, str]] = set()
    for edge in relationships:
        subject = edge.get("subject_entity_id")
        object_ = edge.get("object_entity_id")
        if (
            isinstance(subject, str)
            and isinstance(object_, str)
            and subject in entity_ids
            and object_ in entity_ids
            and subject != object_
        ):
            degrees[subject] += 1
            degrees[object_] += 1
            valid_edges += 1
            unique_pairs.add((subject, object_))
    count = len(entity_ids)
    possible = count * (count - 1)
    return GraphPatternSummary(
        entity_count=count,
        relationship_count=valid_edges,
        average_degree=sum(degrees.values()) / count if count else 0.0,
        directed_density=len(unique_pairs) / possible if possible else 0.0,
        degree_counts=dict(degrees),
    )


class PatternTaskInput(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PatternTaskOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: GraphPatternSummary
    limitations: list[str] = Field(default_factory=lambda: [
        "Counts describe recorded graph structure, including unverified candidate links.",
        "Structural measurements do not establish evidence strength, wrongdoing, or causation.",
    ])


async def analyze_case_graph(context: TaskContext, task_input: BaseModel) -> PatternTaskOutput:
    PatternTaskInput.model_validate(task_input)
    entities = await EntitiesRepository(context.database).list_for_case(context.case_id, context.tenant_id)
    relationships = await RelationshipsRepository(context.database).list_for_case(context.case_id, context.tenant_id)
    return PatternTaskOutput(summary=summarize_graph(entities, relationships))


task_registry.register(TaskDefinition(
    task_type=TaskType.ANALYZE_GRAPH_PATTERNS,
    input_model=PatternTaskInput,
    output_model=PatternTaskOutput,
    timeout_seconds=30,
    handler=analyze_case_graph,
))
