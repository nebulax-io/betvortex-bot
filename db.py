"""
BetVortex — Shared Database Module
Lazy initialization — connects on first use, not at import time.
"""

import os
import logging
from supabase import create_client, Client

logger = logging.getLogger(__name__)

_supabase_client = None

def get_client() -> Client:
    """Get or create Supabase client (lazy init)."""
    global _supabase_client
    if _supabase_client is None:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        if not url or not key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY environment variables are required")
        _supabase_client = create_client(url, key)
        logger.info("Supabase client initialized")
    return _supabase_client

class _SupabaseProxy:
    """Proxy that lazy-inits Supabase client on first table() call."""
    def __getattr__(self, name):
        return getattr(get_client(), name)

supabase = _SupabaseProxy()
