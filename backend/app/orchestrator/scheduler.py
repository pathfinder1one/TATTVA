from app.domain.task_spec import TaskSpec


def ready_batches(specs: list[TaskSpec], max_concurrent: int) -> list[list[TaskSpec]]:
    """Return deterministic dependency-ready batches without model-controlled routing."""
    if max_concurrent < 1:
        raise ValueError("At least one task slot is required.")
    by_id = {item.task_id: item for item in specs}
    remaining = set(by_id)
    completed: set[str] = set()
    batches: list[list[TaskSpec]] = []
    while remaining:
        ready_ids = sorted(
            task_id for task_id in remaining
            if set(by_id[task_id].depends_on) <= completed
        )
        if not ready_ids:
            raise ValueError("No dependency-ready task remains.")
        for index in range(0, len(ready_ids), max_concurrent):
            batch = [by_id[task_id] for task_id in ready_ids[index:index + max_concurrent]]
            batches.append(batch)
            completed.update(item.task_id for item in batch)
            remaining.difference_update(item.task_id for item in batch)
    return batches
