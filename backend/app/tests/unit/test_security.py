import pytest
from fastapi import HTTPException

from app.core.security import require_safe_identifier


@pytest.mark.parametrize("value", ["case-1", "actor.name", "tenant:42"])
def test_safe_identifiers_are_trimmed(value):
    assert require_safe_identifier(f" {value} ", "case ID") == value


@pytest.mark.parametrize("value", [None, "", "bad/id", "space value", "a\nadmin", 42])
def test_unsafe_identifiers_are_rejected(value):
    with pytest.raises(HTTPException) as exc:
        require_safe_identifier(value, "case ID")
    assert exc.value.status_code == 401
