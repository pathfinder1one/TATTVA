from app.config import Settings
from app.domain.task_spec import TaskSpec
from app.orchestrator.task_registry import TaskRegistry


def validate_plan(specs: list[TaskSpec], settings: Settings, registry: TaskRegistry) -> None:
    if not specs or len(specs) > settings.max_tasks_per_run:
        raise ValueError("Plan task count is outside the configured run limit.")
    by_id = {item.task_id: item for item in specs}
    if len(by_id) != len(specs):
        raise ValueError("Task IDs in a plan must be unique.")

    for spec in specs:
        definition = registry.get(spec.task_type)
        if spec.timeout_seconds > settings.max_task_timeout_seconds:
            raise ValueError("Task timeout exceeds the configured run limit.")
        if spec.timeout_seconds > definition.timeout_seconds:
            raise ValueError("Task timeout exceeds the registered task limit.")
        if spec.retry_limit > settings.max_retries_per_task:
            raise ValueError("Task retry limit exceeds the configured run limit.")
        if any(dependency not in by_id for dependency in spec.depends_on):
            raise ValueError("A task refers to a dependency outside this plan.")

    completed: set[str] = set()
    remaining = set(by_id)
    while remaining:
        ready = {task_id for task_id in remaining if set(by_id[task_id].depends_on) <= completed}
        if not ready:
            raise ValueError("Task plan contains a dependency cycle.")
        completed.update(ready)
        remaining.difference_update(ready)
