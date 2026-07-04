"""
Supabase async client singleton.

Uses the SERVICE ROLE KEY (bypasses RLS) so the backend can read/write on
behalf of any authenticated user.  The user's identity has already been
verified by the JWT middleware before any repo call is made.
"""

import os
from typing import Optional

from supabase import AsyncClient, acreate_client

_client: Optional[AsyncClient] = None


async def get_supabase_client() -> AsyncClient:
    global _client
    if _client is None:
        url = os.getenv("SUPABASE_URL", "").rstrip("/")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
        if not url or not key:
            raise RuntimeError(
                "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set"
            )
        _client = await acreate_client(url, key)
    return _client
