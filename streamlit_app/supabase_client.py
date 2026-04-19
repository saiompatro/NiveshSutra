"""
Supabase client factory.

- get_anon_client()          -> public read operations (no RLS bypass)
- get_authed_client(token)   -> user-specific tables with RLS (uses JWT)
- get_admin_client()         -> service-role operations (bypasses RLS)
"""

from functools import lru_cache

from config import get_required_setting, get_setting

SUPABASE_URL = get_required_setting("SUPABASE_URL")
SUPABASE_ANON_KEY = get_required_setting("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_ROLE_KEY = get_setting("SUPABASE_SERVICE_ROLE_KEY")


@lru_cache(maxsize=1)
def get_anon_client():
    from supabase import create_client

    return create_client(SUPABASE_URL, SUPABASE_ANON_KEY)


def get_authed_client(access_token: str):
    """Return a Supabase client that sends the user JWT on every PostgREST call."""
    from supabase import create_client

    client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    client.postgrest.auth(access_token)
    return client


@lru_cache(maxsize=1)
def get_admin_client():
    from supabase import create_client

    key = SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY
    return create_client(SUPABASE_URL, key)
