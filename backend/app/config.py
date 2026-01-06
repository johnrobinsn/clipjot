"""Configuration management for ClipJot.

Loads configuration from environment variables with .env file support.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root
_project_root = Path(__file__).parent.parent.parent
_env_file = _project_root / ".env"
if _env_file.exists():
    load_dotenv(_env_file)


def _get_env(key: str, default: str | None = None, required: bool = False) -> str | None:
    """Get environment variable with optional default and required check."""
    value = os.getenv(key, default)
    if required and not value:
        raise ValueError(f"Required environment variable {key} is not set")
    return value


def _get_int(key: str, default: int) -> int:
    """Get integer environment variable."""
    value = os.getenv(key)
    if value is None:
        return default
    return int(value)


# Application settings
SECRET_KEY: str = _get_env("SECRET_KEY", required=True)
DATABASE_PATH: str = _get_env("DATABASE_PATH", "./clipjot.db")
BASE_URL: str = _get_env("BASE_URL", "http://localhost:5001")

# Google OAuth
GOOGLE_CLIENT_ID: str | None = _get_env("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET: str | None = _get_env("GOOGLE_CLIENT_SECRET")

# GitHub OAuth
GITHUB_CLIENT_ID: str | None = _get_env("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET: str | None = _get_env("GITHUB_CLIENT_SECRET")

# Rate limiting
RATE_LIMIT_REQUESTS: int = _get_int("RATE_LIMIT_REQUESTS", 100)
RATE_LIMIT_WINDOW: int = _get_int("RATE_LIMIT_WINDOW", 60)

# Session settings
SESSION_MAX_AGE: int = _get_int("SESSION_MAX_AGE", 2592000)  # 30 days

# Free tier limits
FREE_TIER_MAX_BOOKMARKS: int = _get_int("FREE_TIER_MAX_BOOKMARKS", 1000)
FREE_TIER_MAX_TAGS: int = _get_int("FREE_TIER_MAX_TAGS", 50)


def has_google_oauth() -> bool:
    """Check if Google OAuth is configured."""
    return bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET)


def has_github_oauth() -> bool:
    """Check if GitHub OAuth is configured."""
    return bool(GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET)
