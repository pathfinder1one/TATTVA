"""Local development identity and configurable OIDC/JWKS bearer verification."""

from functools import lru_cache
from urllib.parse import urlparse

import jwt
from fastapi import HTTPException, status
from jwt import PyJWKClient
from jwt.exceptions import PyJWKClientConnectionError, PyJWKClientError, PyJWTError

from app.config import Settings
from app.core.security import require_safe_identifier
from app.core.identity import Actor


@lru_cache(maxsize=8)
def _jwks_client(url: str, timeout_seconds: int) -> PyJWKClient:
    return PyJWKClient(url, timeout=timeout_seconds, cache_keys=True)


def resolve_actor(
    settings: Settings,
    *,
    authorization: str | None,
    x_user_id: str | None = None,
    x_tenant_id: str | None = None,
) -> Actor:
    """Return a verified actor; trust identity headers only in local development."""
    if settings.app_env == "development" and settings.local_auth_enabled and not authorization:
        if not x_user_id or not x_tenant_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Set X-User-Id and X-Tenant-Id for local development requests.",
            )
        return Actor(
            user_id=require_safe_identifier(x_user_id, "user ID"),
            tenant_id=require_safe_identifier(x_tenant_id, "tenant ID"),
        )

    if not (settings.auth_jwks_url and settings.auth_issuer and settings.auth_audience):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Bearer authentication is not configured.",
        )
    if settings.app_env != "development" and (
        urlparse(settings.auth_jwks_url).scheme != "https"
        or urlparse(settings.auth_issuer).scheme != "https"
    ):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Production identity endpoints must use HTTPS.",
        )
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="A valid bearer token is required.",
        )
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="A valid bearer token is required.",
        )

    try:
        client = _jwks_client(settings.auth_jwks_url, settings.auth_jwks_timeout_seconds)
        signing_key = client.get_signing_key_from_jwt(token.strip()).key
        claims = jwt.decode(
            token.strip(),
            signing_key,
            algorithms=["RS256"],
            issuer=settings.auth_issuer,
            audience=settings.auth_audience,
            options={"require": ["exp", "sub"]},
        )
    except PyJWKClientConnectionError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Identity provider is unavailable.",
        ) from exc
    except (PyJWTError, PyJWKClientError, ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer token is invalid or expired.",
        ) from exc

    user_id = claims.get(settings.auth_user_id_claim)
    tenant_id = claims.get(settings.auth_tenant_id_claim)
    if not isinstance(user_id, str) or not isinstance(tenant_id, str):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer token is missing required user or tenant claims.",
        )
    return Actor(
        user_id=require_safe_identifier(user_id, "user ID"),
        tenant_id=require_safe_identifier(tenant_id, "tenant ID"),
    )
