from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domain.task_spec import TaskType
from app.llm.hosted_provider import get_core_provider
from app.llm.prompts import HYPOTHESIS_SYSTEM
from app.orchestrator.task_registry import TaskContext, TaskDefinition, task_registry
from app.schemas.responses import SearchCitation


class HypothesisEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    citation_id: str = Field(min_length=1, max_length=140)
    quote: str = Field(min_length=1, max_length=2000)
    start_offset: int = Field(ge=0)
    end_offset: int = Field(gt=0)

    @model_validator(mode="after")
    def valid_range(self):
        if self.end_offset <= self.start_offset or self.end_offset - self.start_offset != len(self.quote):
            raise ValueError("Hypothesis evidence offsets must match the quote length.")
        return self


class HypothesisSuggestion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    statement: str = Field(min_length=5, max_length=1000)
    evidence_for: list[HypothesisEvidence] = Field(min_length=1, max_length=20)
    evidence_against: list[HypothesisEvidence] = Field(min_length=1, max_length=20)
    unknowns: list[str] = Field(default_factory=list, max_length=20)
    status: str = "unverified_hypothesis"


class HypothesisOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    hypotheses: list[HypothesisSuggestion] = Field(default_factory=list, max_length=20)
    limitations: list[str] = Field(default_factory=list, max_length=20)

    @model_validator(mode="after")
    def hypotheses_are_balanced(self):
        for hypothesis in self.hypotheses:
            positive = {(item.citation_id, item.start_offset, item.end_offset) for item in hypothesis.evidence_for}
            negative = {(item.citation_id, item.start_offset, item.end_offset) for item in hypothesis.evidence_against}
            if positive & negative:
                raise ValueError("The same source span cannot support and oppose a hypothesis.")
        return self


def validate_hypothesis_sources(output: HypothesisOutput, citations: dict[str, SearchCitation]) -> HypothesisOutput:
    """Reject unknown citation IDs and quotes that do not resolve exactly."""
    for hypothesis in output.hypotheses:
        for reference in [*hypothesis.evidence_for, *hypothesis.evidence_against]:
            citation = citations.get(reference.citation_id)
            if citation is None:
                raise ValueError("Hypothesis references a source outside this retrieval result.")
            start = reference.start_offset - citation.start_offset
            end = reference.end_offset - citation.start_offset
            if start < 0 or end > len(citation.text) or citation.text[start:end] != reference.quote:
                raise ValueError("Hypothesis evidence quote does not match its exact source span.")
    return output


class HypothesisInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    query: str = Field(min_length=2, max_length=2000)


async def suggest_hypotheses(context: TaskContext, task_input: BaseModel) -> HypothesisOutput:
    request = HypothesisInput.model_validate(task_input)
    source_outputs = [
        value for value in context.dependency_outputs.values()
        if isinstance(value, dict) and isinstance(value.get("citations"), list)
    ]
    if len(source_outputs) != 1:
        raise ValueError("Hypothesis generation requires exactly one retrieval dependency.")
    citations = [SearchCitation.model_validate(item) for item in source_outputs[0]["citations"]]
    if not citations:
        return HypothesisOutput(limitations=["No source passages were retrieved."])
    provider = get_core_provider(context.settings)
    proposed = await provider.generate_structured(
        system=HYPOTHESIS_SYSTEM,
        input_data={
            "query": request.query,
            "output_schema": HypothesisOutput.model_json_schema(),
            "source_excerpts": [citation.model_dump(mode="json") for citation in citations],
        },
        schema=HypothesisOutput,
        timeout_s=context.settings.core_llm_timeout_seconds,
        max_output_tokens=context.settings.core_llm_max_output_tokens,
    )
    output = HypothesisOutput.model_validate(proposed)
    validate_hypothesis_sources(output, {item.citation_id: item for item in citations})
    output.limitations = list(dict.fromkeys([
        *output.limitations,
        "Hypotheses are unverified, advisory suggestions and were not written to the evidence graph.",
        "Source spans on both sides are required; an authorized human must assess their meaning and context.",
    ]))[:20]
    return output


task_registry.register(TaskDefinition(
    task_type=TaskType.SUGGEST_HYPOTHESES,
    input_model=HypothesisInput,
    output_model=HypothesisOutput,
    timeout_seconds=180,
    handler=suggest_hypotheses,
))
