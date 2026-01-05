from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from fastapi import Depends, Header, HTTPException, status

from src.api.core.supabase_client import get_supabase_admin_client


@dataclass(frozen=True)
class AuthContext:
    """Information about the authenticated user."""

    user_id: str
    email: Optional[str] = None


# PUBLIC_INTERFACE
def get_auth_context(authorization: str = Header(default=""),) -> AuthContext:
    """Resolve the authenticated user from a Supabase JWT bearer token.

    The frontend should send:
        Authorization: Bearer <access_token>

    Args:
        authorization: Raw Authorization header value.

    Returns:
        AuthContext containing at least the user_id.

    Raises:
        HTTPException(401): If missing/invalid token.
        HTTPException(500): If Supabase auth check fails unexpectedly.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header.",
        )

    scheme_prefix = "bearer "
    if not authorization.lower().startswith(scheme_prefix):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header must be a Bearer token.",
        )

    token = authorization[len(scheme_prefix) :].strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer token is empty.",
        )

    sb = get_supabase_admin_client()

    try:
        # Supabase client validates token by calling Supabase Auth.
        resp = sb.auth.get_user(token)
        user = getattr(resp, "user", None) or (resp.get("user") if isinstance(resp, dict) else None)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token.",
            )

        user_id = getattr(user, "id", None) or (user.get("id") if isinstance(user, dict) else None)
        email = getattr(user, "email", None) or (user.get("email") if isinstance(user, dict) else None)

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token verified but user id missing.",
            )

        return AuthContext(user_id=user_id, email=email)
    except HTTPException:
        raise
    except Exception as e:
        # Avoid leaking internal errors; provide actionable message.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate token with Supabase Auth: {type(e).__name__}",
        ) from e


# PUBLIC_INTERFACE
def require_auth(ctx: AuthContext = Depends(get_auth_context)) -> AuthContext:
    """FastAPI dependency enforcing auth.

    Returns:
        AuthContext for downstream handlers.
    """
    return ctx
