from __future__ import annotations

import os
from dataclasses import dataclass

from supabase import Client, create_client


@dataclass(frozen=True)
class SupabaseSettings:
    """Runtime settings for Supabase access."""

    url: str
    service_role_key: str


# PUBLIC_INTERFACE
def get_supabase_settings() -> SupabaseSettings:
    """Load Supabase settings from environment variables.

    Required env vars:
    - SUPABASE_URL
    - SUPABASE_SERVICE_ROLE_KEY

    Returns:
        SupabaseSettings

    Raises:
        RuntimeError: If required variables are missing.
    """
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise RuntimeError(
            "Missing Supabase configuration. Please set SUPABASE_URL and "
            "SUPABASE_SERVICE_ROLE_KEY in the backend environment."
        )
    return SupabaseSettings(url=url, service_role_key=key)


# PUBLIC_INTERFACE
def get_supabase_admin_client() -> Client:
    """Create a Supabase client using the service role key.

    Notes:
        - This is intended for server-side usage only.
        - We still verify end-user JWTs separately (auth.get_user(token)).
    """
    settings = get_supabase_settings()
    return create_client(settings.url, settings.service_role_key)
