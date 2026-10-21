from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domain.enums import EntityType
from app.domain.task_spec import TaskType
from app.llm.hosted_provider import get_core_provider
from app.llm.prompts import ENTITY_EXTRACTION_SYSTEM
from app.orchestrator.task_registry import TaskContext, TaskDefinition, task_registry
from app.schemas.responses import SearchCitation


class CandidateMention(BaseModel):
    model_config = ConfigDict(extra="forbid")

    entity_type: EntityType
    display_name: str = Field(min_length=1, max_length=200)
    citation_id: str = Field(min_length=1, max_length=140)
    quote: str = Field(min_length=1, max_length=2000)
    start_offset: int = Field(ge=0)
    end_offset: int = Field(gt=0)

    @model_validator(mode="after")
    def valid_range(self):
        if self.end_offset <= self.start_offset:
            raise ValueError("Candidate mention offsets must be increasing.")
        return self


class CandidateRelationship(BaseModel):
    model_config = ConfigDict(extra="forbid")

    subject_name: str = Field(min_length=1, max_length=200)
    predicate: str = Field(min_length=1, max_length=120)
    object_name: str = Field(min_length=1, max_length=200)
    citation_id: str = Field(min_length=1, max_length=140)
    quote: str = Field(min_length=1, max_length=2000)
    start_offset: int = Field(ge=0)
    end_offset: int = Field(gt=0)

    @model_validator(mode="after")
    def valid_range(self):
        if self.end_offset <= self.start_offset:
            raise ValueError("Candidate relationship offsets must be increasing.")
        if self.subject_name.casefold() == self.object_name.casefold():
            raise ValueError("A candidate relationship must connect distinct names.")
        return self


class ExtractionInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=2, max_length=2000)


class ExtractionOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["candidate_only"] = "candidate_only"
    mentions: list[CandidateMention] = Field(default_factory=list, max_length=100)
    relationships: list[CandidateRelationship] = Field(default_factory=list, max_length=100)
    limitations: list[str] = Field(default_factory=list, max_length=20)


async def extract_candidates(context: TaskContext, task_input: BaseModel) -> ExtractionOutput:
    request = ExtractionInput.model_validate(task_input)
    source_outputs = [
        value for value in context.dependency_outputs.values()
        if isinstance(value, dict) and isinstance(value.get("citations"), list)
    ]
    if len(source_outputs) != 1:
        raise ValueError("Extraction requires exactly one completed retrieval dependency.")
    citations = [SearchCitation.model_validate(item) for item in source_outputs[0]["citations"]]
    if not citations:
        return ExtractionOutput(limitations=["No source passages were retrieved."])
    provider = get_core_provider(context.settings)
    proposed = await provider.generate_structured(
        system=ENTITY_EXTRACTION_SYSTEM,
        input_data={
            "query": request.query,
            "output_schema": ExtractionOutput.model_json_schema(),
            "source_excerpts": [citation.model_dump(mode="json") for citation in citations],
        },
        schema=ExtractionOutput,
        timeout_s=context.settings.core_llm_timeout_seconds,
        max_output_tokens=context.settings.core_llm_max_output_tokens,
    )
    output = ExtractionOutput.model_validate(proposed)
    citations_by_id = {citation.citation_id: citation for citation in citations}
    for item in [*output.mentions, *output.relationships]:
        citation = citations_by_id.get(item.citation_id)
        if citation is None:
            raise ValueError("Extraction output cited a passage outside the retrieval result.")
        local_start = item.start_offset - citation.start_offset
        local_end = item.end_offset - citation.start_offset
        if (
            local_start < 0
            or local_end > len(citation.text)
            or local_end <= local_start
            or citation.text[local_start:local_end] != item.quote
        ):
            raise ValueError("Extraction output did not resolve to an exact source quote.")
        if isinstance(item, CandidateMention) and item.display_name.casefold() not in item.quote.casefold():
            raise ValueError("Extracted entity name is not present in its supporting quote.")
        if isinstance(item, CandidateRelationship) and (
            item.subject_name.casefold() not in item.quote.casefold()
            or item.object_name.casefold() not in item.quote.casefold()
        ):
            raise ValueError("Relationship quote does not explicitly name both entities.")
    output.limitations = list(dict.fromkeys([
        *output.limitations,
        "Candidates are unverified and were not written to the evidence graph.",
        "An authorized human must review any candidate before it becomes a case record.",
    ]))[:20]
    return output


task_registry.register(
    TaskDefinition(
        task_type=TaskType.EXTRACT_CANDIDATES,
        input_model=ExtractionInput,
        output_model=ExtractionOutput,
        timeout_seconds=180,
        handler=extract_candidates,
    )
)
