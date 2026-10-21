"""Compare extracted candidate relationship values without asserting conflict."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.agents.contradiction_analyst import (
    PotentialContradiction, ClaimValue, find_explicit_value_conflicts,
)
from app.agents.entity_resolution import normalize_entity_name
from app.domain.task_spec import TaskType
from app.orchestrator.task_registry import TaskContext, TaskDefinition, task_registry
from app.schemas.responses import SearchCitation


class CandidateComparisonInput(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CandidateComparisonOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    potential_value_discrepancies: list[PotentialContradiction] = Field(default_factory=list, max_length=100)
    source_reference_note: str = (
        "Claim evidence_id values are retrieval citation IDs, not persisted evidence records. "
        "Each discrepancy is a review lead, not proof that two claims conflict."
    )
    limitations: list[str] = Field(default_factory=lambda: [
        "Different values for the same normalized subject and predicate may both be true.",
        "An authorized investigator must inspect the source passages and decide whether a contradiction exists.",
    ])


async def compare_candidate_relationships(
    context: TaskContext, task_input: BaseModel
) -> CandidateComparisonOutput:
    CandidateComparisonInput.model_validate(task_input)
    dependency_outputs = [
        output for output in context.dependency_outputs.values()
        if isinstance(output, dict)
    ]
    extraction_outputs = [output for output in dependency_outputs if isinstance(output.get("relationships"), list)]
    retrieval_outputs = [output for output in dependency_outputs if isinstance(output.get("citations"), list)]
    if len(extraction_outputs) != 1 or len(retrieval_outputs) != 1:
        raise ValueError("Candidate comparison requires one extraction and one retrieval dependency.")
    claims: list[dict[str, Any]] = []
    for relationship in extraction_outputs[0]["relationships"]:
        citation_id = relationship.get("citation_id")
        subject = relationship.get("subject_name")
        predicate = relationship.get("predicate")
        value = relationship.get("object_name")
        if not all(isinstance(item, str) and item.strip() for item in (citation_id, subject, predicate, value)):
            continue
        claims.append({
            "subject_id": normalize_entity_name(subject),
            "predicate": normalize_entity_name(predicate),
            "value": normalize_entity_name(value),
            "evidence_id": citation_id,
        })
    discrepancies = find_explicit_value_conflicts(claims)
    citations = [item for item in retrieval_outputs[0]["citations"] if isinstance(item, dict)]
    allowed_ids = {citation.citation_id for citation in (SearchCitation.model_validate(c) for c in citations)}
    if any(
        claim.evidence_id not in allowed_ids
        for item in discrepancies for claim in item.claims
    ):
        raise ValueError("Candidate comparison returned an unknown source citation.")
    return CandidateComparisonOutput(potential_value_discrepancies=discrepancies)


task_registry.register(TaskDefinition(
    task_type=TaskType.COMPARE_CANDIDATES,
    input_model=CandidateComparisonInput,
    output_model=CandidateComparisonOutput,
    timeout_seconds=30,
    handler=compare_candidate_relationships,
))
