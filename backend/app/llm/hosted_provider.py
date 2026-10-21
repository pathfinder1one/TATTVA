import json
from typing import Type

import httpx
from pydantic import BaseModel

from app.config import Settings
from app.llm.core_provider import CoreLLMProvider
from app.llm.output_validation import validate_structured_output


class HostedProviderError(RuntimeError):
    """Provider failure without response bodies, prompts, or credentials."""


class OpenAICompatibleProvider:
    """Minimal chat-completions adapter for OpenAI-compatible hosted APIs."""

    def __init__(self, settings: Settings):
        if not settings.core_llm_configured:
            raise ValueError("Core LLM provider is not fully configured.")
        self.base_url = settings.core_llm_base_url.rstrip("/")
        self.api_key = settings.core_llm_api_key
        self.model = settings.core_llm_model

    async def generate_structured(
        self, *, system: str, input_data: dict, schema: Type[BaseModel],
        timeout_s: float, max_output_tokens: int
    ) -> BaseModel:
        raw = await self._complete(
            system=system,
            messages=[{"role": "user", "content": json.dumps(input_data, ensure_ascii=False)}],
            timeout_s=timeout_s,
            max_output_tokens=max_output_tokens,
            response_format={"type": "json_object"},
        )
        return validate_structured_output(raw, schema)

    async def generate_text(
        self, *, system: str, messages: list[dict[str, str]],
        timeout_s: float, max_output_tokens: int
    ) -> str:
        return await self._complete(
            system=system, messages=messages, timeout_s=timeout_s,
            max_output_tokens=max_output_tokens,
        )

    async def _complete(
        self, *, system: str, messages: list[dict[str, str]], timeout_s: float,
        max_output_tokens: int, response_format: dict | None = None
    ) -> str:
        if not 1 <= timeout_s <= 600 or not 1 <= max_output_tokens <= 32_000:
            raise ValueError("Provider call limits are outside the supported range.")
        payload = {
            "model": self.model,
            "messages": [{"role": "system", "content": system}, *messages],
            "temperature": 0,
            "max_tokens": max_output_tokens,
        }
        if response_format:
            payload["response_format"] = response_format
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(timeout_s)) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"}, json=payload,
                )
                response.raise_for_status()
                body = response.json()
            content = body["choices"][0]["message"]["content"]
            if not isinstance(content, str) or not content.strip():
                raise HostedProviderError("Core LLM returned an empty response.")
            return content
        except HostedProviderError:
            raise
        except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError) as exc:
            raise HostedProviderError("Core LLM request failed or returned an invalid response.") from exc


def get_core_provider(settings: Settings) -> CoreLLMProvider:
    return OpenAICompatibleProvider(settings)
