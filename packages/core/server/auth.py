"""
JWT authentication middleware for Axiom API.

Verifies Supabase-issued JWTs using Supabase's JWKS endpoint — works with
all Supabase key types (ES256, RS256, HS256) without needing a shared secret.

Dev mode: when SUPABASE_URL is not set, every request is accepted and
attributed to the fixed dev user ID.
"""

import os

from fastapi import Header, HTTPException

_SUPABASE_URL: str = os.getenv("SUPABASE_URL", "").rstrip("/")
_DEV_MODE: bool = not _SUPABASE_URL
_DEV_USER_ID: str = "dev-user"

# PyJWKClient caches keys in-process and refetches on key rotation
_jwks_client = None
if not _DEV_MODE:
    from jwt import PyJWKClient
    _jwks_client = PyJWKClient(
        f"{_SUPABASE_URL}/auth/v1/.well-known/jwks.json",
        cache_keys=True,
    )


async def get_current_user(authorization: str | None = Header(default=None)) -> str:
    """
    FastAPI dependency — validates the Supabase JWT and returns the user_id (sub).

    Dev mode (SUPABASE_URL not set): returns 'dev-user' unconditionally.
    Prod mode: verifies the token against Supabase's JWKS endpoint.
    """
    if _DEV_MODE:
        return _DEV_USER_ID

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing Authorization header. Expected: Bearer <access_token>",
        )

    token = authorization[7:]  # strip "Bearer "

    try:
        import jwt

        signing_key = _jwks_client.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["ES256", "RS256", "HS256"],
            audience="authenticated",
        )
        user_id: str | None = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Token is missing 'sub' claim")
        return user_id
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=401, detail=f"Invalid or expired token: {exc}")


async def get_current_user_context(authorization: str | None = Header(default=None)) -> dict:
    """Return authenticated user context with id + email claims."""
    if _DEV_MODE:
        return {
            "user_id": _DEV_USER_ID,
            "email": "dev-user@local",
            "raw_claims": {"sub": _DEV_USER_ID, "email": "dev-user@local"},
        }

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing Authorization header. Expected: Bearer <access_token>",
        )

    token = authorization[7:]
    try:
        import jwt

        signing_key = _jwks_client.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["ES256", "RS256", "HS256"],
            audience="authenticated",
        )
        user_id: str | None = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Token is missing 'sub' claim")
        return {
            "user_id": user_id,
            "email": payload.get("email") or "",
            "raw_claims": payload,
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=401, detail=f"Invalid or expired token: {exc}")
