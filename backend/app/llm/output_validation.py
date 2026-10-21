import json
from typing import Type

from pydantic import BaseModel, ValidationError

MAX_STRUCTURED_RESPONSE_BYTES = 1_000_000


class StructuredOutputError(ValueError):
    """Safe provider-independent error for malformed model output."""


def validate_structured_output(raw: str | dict, schema: Type[BaseModel]) -> BaseModel:
    if isinstance(raw, str):
        if len(raw.encode("utf-8")) > MAX_STRUCTURED_RESPONSE_BYTES:
            raise StructuredOutputError("Structured model output exceeds the size limit.")
        try:
            value = json.loads(raw)
        except (json.JSONDecodeError, RecursionError) as exc:
            raise StructuredOutputError("Structured model output is not valid JSON.") from exc
    elif isinstance(raw, dict):
        value = raw
    else:
        raise StructuredOutputError("Structured model output has an unsupported type.")
    try:
        return schema.model_validate(value)
    except ValidationError as exc:
        raise StructuredOutputError("Structured model output does not match its schema.") from exc
