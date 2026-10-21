from app.config import Settings
from app.domain.task_spec import TaskSpec, TaskType
from uuid import uuid4


def plan_analysis(query: str, top_k: int, settings: Settings) -> list[TaskSpec]:
    """Build a deterministic DAG; only add model extraction when configured.

    The hosted model cannot create tasks or change task permissions. Candidate
    comparison consumes only validated extraction and retrieved citations.
    """
    retrieval_id = f"task_{uuid4().hex}"
    retrieval = TaskSpec(
        task_id=retrieval_id,
        task_type=TaskType.RETRIEVE_SOURCES,
        inputs={"query": query, "top_k": top_k},
        timeout_seconds=min(45, settings.max_task_timeout_seconds),
        retry_limit=settings.max_retries_per_task,
    )
    specs = [retrieval]
    include_pattern_summary = (
        len(specs) < settings.max_tasks_per_run
        and (not settings.core_llm_configured or settings.max_tasks_per_run >= 3)
    )
    if include_pattern_summary:
        specs.append(TaskSpec(
            task_id=f"task_{uuid4().hex}",
            task_type=TaskType.ANALYZE_GRAPH_PATTERNS,
            inputs={},
            timeout_seconds=min(30, settings.max_task_timeout_seconds),
            retry_limit=settings.max_retries_per_task,
        ))
    extraction_id = None
    if settings.core_llm_configured and len(specs) < settings.max_tasks_per_run:
        extraction_id = f"task_{uuid4().hex}"
        specs.append(TaskSpec(
            task_id=extraction_id,
            task_type=TaskType.EXTRACT_CANDIDATES,
            inputs={"query": query},
            depends_on=[retrieval_id],
            timeout_seconds=min(settings.core_llm_timeout_seconds, settings.max_task_timeout_seconds),
            retry_limit=settings.max_retries_per_task,
        ))
    if extraction_id and len(specs) < settings.max_tasks_per_run:
        specs.append(TaskSpec(
            task_id=f"task_{uuid4().hex}",
            task_type=TaskType.COMPARE_CANDIDATES,
            inputs={},
            depends_on=[retrieval_id, extraction_id],
            timeout_seconds=min(30, settings.max_task_timeout_seconds),
            retry_limit=settings.max_retries_per_task,
        ))
    if settings.core_llm_configured and len(specs) < settings.max_tasks_per_run:
        specs.append(TaskSpec(
            task_id=f"task_{uuid4().hex}",
            task_type=TaskType.SUGGEST_HYPOTHESES,
            inputs={"query": query},
            depends_on=[retrieval_id],
            timeout_seconds=min(settings.core_llm_timeout_seconds, settings.max_task_timeout_seconds),
            retry_limit=settings.max_retries_per_task,
        ))
    return specs
