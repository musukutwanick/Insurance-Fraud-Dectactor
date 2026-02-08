"""
Supabase client initialization.

DISABLED - Using local file storage only.
"""

from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Supabase is disabled - using local storage
_supabase = None

logger.info("Supabase disabled - using local file storage")


def get_supabase_client():
    """Always returns None - Supabase disabled."""
    return None


def is_supabase_configured() -> bool:
    """Always returns False - using local storage only."""
    return False
