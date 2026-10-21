from datetime import datetime, timedelta, timezone

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException

from app.api.v1 import auth
from app.config import Settings
from app.core.identity import Actor


class _SigningKey:
    def __init__(self, key):
        self.key = key


class _FakeJwksClient:
    def __init__(self, key):
        self.key = key

    def get_signing_key_from_jwt(self, _token):
        return _SigningKey(self.key)


def _token(private_key, *, expires_at=None, tenant="tenant-a"):
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "iss": "https://identity.example.test/",
            "aud": "tattva-api",
            "sub": "investigator-1",
            "tenant_id": tenant,
            "iat": now,
            "exp": expires_at or now + timedelta(minutes=5),
        },
        private_key,
        algorithm="RS256",
        headers={"kid": "test-key"},
    )


@pytest.fixture
def rsa_keys():
    private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return private, private.public_key()


def test_development_identity_uses_local_headers():
    settings = Settings(_env_file=None, app_env="development", local_auth_enabled=True)
    actor = auth.resolve_actor(
        settings, authorization=None, x_user_id=" user-1 ", x_tenant_id="tenant-1"
    )
    assert actor == Actor(user_id="user-1", tenant_id="tenant-1")


def test_local_headers_are_rejected_outside_development():
    settings = Settings(
        _env_file=None,
        app_env="production",
        auth_jwks_url="https://identity.example.test/jwks",
        auth_issuer="https://identity.example.test/",
        auth_audience="tattva-api",
    )
    with pytest.raises(HTTPException) as exc:
        auth.resolve_actor(settings, authorization=None, x_user_id="spoof", x_tenant_id="tenant")
    assert exc.value.status_code == 401


def test_missing_production_auth_configuration_fails_closed():
    settings = Settings(_env_file=None, app_env="production")
    with pytest.raises(HTTPException) as exc:
        auth.resolve_actor(settings, authorization="Bearer abc")
    assert exc.value.status_code == 503


def test_valid_oidc_bearer_maps_configured_identity_claims(monkeypatch, rsa_keys):
    private, public = rsa_keys
    monkeypatch.setattr(auth, "_jwks_client", lambda *_: _FakeJwksClient(public))
    settings = Settings(
        _env_file=None,
        app_env="production",
        auth_jwks_url="https://identity.example.test/jwks",
        auth_issuer="https://identity.example.test/",
        auth_audience="tattva-api",
    )
    actor = auth.resolve_actor(
        settings, authorization=f"Bearer {_token(private)}", x_user_id="spoof", x_tenant_id="spoof"
    )
    assert actor == Actor(user_id="investigator-1", tenant_id="tenant-a")


def test_expired_bearer_is_rejected(monkeypatch, rsa_keys):
    private, public = rsa_keys
    monkeypatch.setattr(auth, "_jwks_client", lambda *_: _FakeJwksClient(public))
    settings = Settings(
        _env_file=None,
        app_env="production",
        auth_jwks_url="https://identity.example.test/jwks",
        auth_issuer="https://identity.example.test/",
        auth_audience="tattva-api",
    )
    token = _token(private, expires_at=datetime.now(timezone.utc) - timedelta(seconds=5))
    with pytest.raises(HTTPException) as exc:
        auth.resolve_actor(settings, authorization=f"Bearer {token}")
    assert exc.value.status_code == 401


def test_tenant_claim_must_be_a_safe_string(monkeypatch, rsa_keys):
    private, public = rsa_keys
    monkeypatch.setattr(auth, "_jwks_client", lambda *_: _FakeJwksClient(public))
    settings = Settings(
        _env_file=None,
        app_env="production",
        auth_jwks_url="https://identity.example.test/jwks",
        auth_issuer="https://identity.example.test/",
        auth_audience="tattva-api",
    )
    token = _token(private, tenant=["tenant-a"])
    with pytest.raises(HTTPException) as exc:
        auth.resolve_actor(settings, authorization=f"Bearer {token}")
    assert exc.value.status_code == 401
