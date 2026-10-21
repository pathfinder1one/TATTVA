from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class SourceQuoteCheck(BaseModel):
    model_config = ConfigDict(extra="forbid")

    result: Literal["exact_match", "invalid"]
    reason: str = Field(max_length=240)


def check_exact_source_quote(
    *, source_text: str, start_offset: int, end_offset: int, quote: str
) -> SourceQuoteCheck:
    """Verify byte-for-byte source integrity; this does not assess claim support."""
    if start_offset < 0 or end_offset <= start_offset or end_offset > len(source_text):
        return SourceQuoteCheck(result="invalid", reason="Offsets are outside the source text.")
    if source_text[start_offset:end_offset] != quote:
        return SourceQuoteCheck(result="invalid", reason="Quote does not match the source at those offsets.")
    return SourceQuoteCheck(result="exact_match", reason="Quote matches the source span exactly.")
