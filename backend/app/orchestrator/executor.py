from pydantic import BaseModel, ConfigDict, Field

from app.agents import extraction as extraction_agent
from app.agents import pattern_analyst as pattern_agent
from app.agents import candidate_comparison as comparison_agent
from app.agents import hypothesis_analyst as hypothesis_agent
from app.domain.task_spec import TaskType
from app.orchestrator.task_registry import TaskContext, TaskDefinition, task_registry
from app.schemas.responses import SearchCitation
from app.services.retrieval_service import search_case


class RetrieveSourcesInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=2, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=20)


class RetrieveSourcesOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str
    citations: list[SearchCitation]
    limitations: list[str]


async def retrieve_sources(context: TaskContext, task_input: BaseModel) -> RetrieveSourcesOutput:
    request = RetrieveSourcesInput.model_validate(task_input)
    citations = await search_case(
        context.database,
        context.qdrant,
        context.settings,
        case_id=context.case_id,
        tenant_id=context.tenant_id,
        query=request.query,
        top_k=request.top_k,
    )
    return RetrieveSourcesOutput(
        query=request.query,
        citations=citations,
        limitations=[
            "This run performs source retrieval only; it does not generate or verify findings.",
            "Semantic retrieval scores are not evidence strength or relationship confidence.",
        ],
    )


task_registry.register(
    TaskDefinition(
        task_type=TaskType.RETRIEVE_SOURCES,
        input_model=RetrieveSourcesInput,
        output_model=RetrieveSourcesOutput,
        timeout_seconds=60,
        handler=retrieve_sources,
    )
)
