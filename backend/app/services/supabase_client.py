"""
Supabase client utility for backend.
Uses service role key for admin operations (bypasses RLS).
"""
import os
from functools import lru_cache

try:
    from supabase import create_client, Client
except ImportError:
    create_client = None
    Client = None


@lru_cache(maxsize=1)
def get_supabase_client() -> "Client | None":
    """
    Get Supabase client with service role key.
    Returns None if not configured (local dev without Supabase).
    """
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")

    if not url or not key:
        return None

    if create_client is None:
        raise RuntimeError("supabase-py not installed. Run: pip install supabase")

    return create_client(url, key)


def get_supabase_admin() -> "Client":
    """Get admin client (raises if not configured)."""
    client = get_supabase_client()
    if client is None:
        raise RuntimeError("Supabase not configured. Set SUPABASE_URL and SUPABASE_SERVICE_KEY")
    return client


# Example usage:
# client = get_supabase_admin()
# user = client.auth.admin.get_user_by_id(user_id)
# bucket = client.storage.from_("uploads")