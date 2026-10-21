import re

from fastapi import HTTPException, status

_SAFE_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:@+-]{0,119}$")


def require_safe_identifier(value: str | None, label: str) -> str:
    """Reject unbounded/control-character identity values before database use."""
    normalized = value.strip() if isinstance(value, str) else ""
    if not _SAFE_IDENTIFIER.fullmatch(normalized):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"A valid {label} is required.",
        )
    return normalized
