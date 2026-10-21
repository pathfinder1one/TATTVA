from typing import Protocol, Type

from pydantic import BaseModel


class CoreLLMProvider(Protocol):
    """Provider-neutral contract shared by orchestration and RAG generation."""

    async def generate_structured(
        self, *, system: str, input_data: dict, schema: Type[BaseModel],
        timeout_s: float, max_output_tokens: int
    ) -> BaseModel: ...

    async def generate_text(
        self, *, system: str, messages: list[dict[str, str]],
        timeout_s: float, max_output_tokens: int
    ) -> str: ...
