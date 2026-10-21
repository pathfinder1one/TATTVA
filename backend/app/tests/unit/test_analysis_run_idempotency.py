import pytest
from fastapi import HTTPException

from app.schemas.requests import AnalysisRunCreateRequest
from app.services.analysis_run_service import (
    request_fingerprint,
    require_matching_idempotent_request,
    validate_idempotency_key,
)


@pytest.mark.parametrize("key", ["request-123", "a" * 128, "job_2026.10:21"])
def test_idempotency_key_accepts_bounded_safe_characters(key):
    assert validate_idempotency_key(key) == key


@pytest.mark.parametrize("key", ["short", "bad/key/with/slash", "has spaces", "a" * 129])
def test_idempotency_key_rejects_unsafe_or_unbounded_values(key):
    with pytest.raises(HTTPException) as exc:
        validate_idempotency_key(key)
    assert exc.value.status_code == 400


def test_fingerprint_is_stable_for_the_same_normalized_request():
    first = AnalysisRunCreateRequest(query="  Find vehicle references  ", top_k=5)
    second = AnalysisRunCreateRequest(query="Find vehicle references", top_k=5)
    assert request_fingerprint(first) == request_fingerprint(second)


def test_reusing_key_with_a_different_fingerprint_conflicts():
    with pytest.raises(HTTPException) as exc:
        require_matching_idempotent_request({"request_fingerprint": "stored"}, "different")
    assert exc.value.status_code == 409


def test_replaying_same_fingerprint_is_allowed():
    require_matching_idempotent_request({"request_fingerprint": "same"}, "same")
