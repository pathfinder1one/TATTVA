from app.config import Settings
from app.domain.task_spec import TaskType
from app.orchestrator.planner import plan_analysis


def test_retrieval_only_plan_is_bounded_and_valid():
    settings = Settings(_env_file=None, max_tasks_per_run=1, max_retries_per_task=0)
    plan = plan_analysis("Find source mentions", 5, settings)
    assert len(plan) == 1
    assert plan[0].task_type == TaskType.RETRIEVE_SOURCES
    assert plan[0].depends_on == []


def test_configured_plan_dependencies_reference_existing_tasks():
    settings = Settings(
        _env_file=None,
        core_llm_base_url="https://llm.example.test/v1",
        core_llm_api_key="unit-test-only",
        core_llm_model="test-model",
        max_tasks_per_run=5,
    )
    plan = plan_analysis("Find source mentions", 5, settings)
    task_ids = {task.task_id for task in plan}
    assert len(plan) <= settings.max_tasks_per_run
    assert all(dependency in task_ids for task in plan for dependency in task.depends_on)
    assert len(task_ids) == len(plan)
