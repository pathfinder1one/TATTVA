from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Type

from pydantic import BaseModel

from app.domain.task_spec import TaskSpec, TaskType


@dataclass(frozen=True)
class TaskContext:
    database: Any
    qdrant: Any
    settings: Any
    case_id: str
    tenant_id: str
    run_id: str
    dependency_outputs: dict[str, dict] = field(default_factory=dict)


TaskHandler = Callable[[TaskContext, BaseModel], Awaitable[BaseModel | dict]]


@dataclass(frozen=True)
class TaskDefinition:
    task_type: TaskType
    input_model: Type[BaseModel]
    output_model: Type[BaseModel]
    timeout_seconds: int
    handler: TaskHandler


class TaskRegistry:
    """Static allowlist; task definitions are registered by trusted application code."""

    def __init__(self):
        self._definitions: dict[TaskType, TaskDefinition] = {}

    def register(self, definition: TaskDefinition) -> None:
        if definition.task_type in self._definitions:
            raise ValueError(f"Task type already registered: {definition.task_type.value}")
        self._definitions[definition.task_type] = definition

    def get(self, task_type: TaskType) -> TaskDefinition:
        try:
            return self._definitions[task_type]
        except KeyError as exc:
            raise ValueError(f"Task type is not registered: {task_type.value}") from exc

    def all(self) -> dict[TaskType, TaskDefinition]:
        return dict(self._definitions)

    async def execute(self, spec: TaskSpec, context: TaskContext) -> dict:
        definition = self.get(spec.task_type)
        task_input = definition.input_model.model_validate(spec.inputs)
        timeout = min(spec.timeout_seconds, definition.timeout_seconds)
        import asyncio

        result = await asyncio.wait_for(definition.handler(context, task_input), timeout=timeout)
        validated = definition.output_model.model_validate(result)
        return validated.model_dump(mode="json")


task_registry = TaskRegistry()
