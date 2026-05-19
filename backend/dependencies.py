from backend.database import get_db, DEFAULT_USER_ID  # noqa: F401


def get_current_user_id() -> str:
    """Return the single local user ID (no auth)."""
    return DEFAULT_USER_ID
