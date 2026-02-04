"""Database models for ClipJot.

Dataclass definitions used by FastLite for table creation and CRUD operations.
"""

import secrets
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class User:
    """User account."""
    id: Optional[int] = None
    email: str = ""
    created_at: Optional[str] = None
    is_premium: bool = False
    is_admin: bool = False
    is_suspended: bool = False
    suspended_at: Optional[str] = None
    suspended_reason: Optional[str] = None


@dataclass
class Credential:
    """OAuth credential linking a provider identity to a user."""
    id: Optional[int] = None
    user_id: int = 0
    provider: str = ""  # 'google' or 'github'
    provider_user_id: str = ""
    created_at: Optional[str] = None


@dataclass
class Session:
    """User session for web UI and client authentication."""
    id: str = ""  # Random session token (primary key)
    user_id: int = 0
    created_at: Optional[str] = None
    expires_at: str = ""
    last_activity_at: Optional[str] = None
    user_agent: Optional[str] = None
    client_name: Optional[str] = None  # 'web', 'chrome-extension', 'android'
    ip_address: Optional[str] = None


@dataclass
class ApiToken:
    """API token for programmatic access."""
    id: Optional[int] = None
    user_id: int = 0
    name: str = ""
    token_hash: str = ""  # SHA-256 hash of the actual token
    scope: str = "read"  # 'read' or 'write'
    created_at: Optional[str] = None
    expires_at: str = ""
    last_used_at: Optional[str] = None


@dataclass
class Tag:
    """User-defined tag for organizing bookmarks."""
    id: Optional[int] = None
    user_id: int = 0
    name: str = ""
    created_at: Optional[str] = None


@dataclass
class Bookmark:
    """A saved bookmark/link."""
    id: Optional[int] = None
    user_id: int = 0
    url: str = ""
    title: Optional[str] = None
    comment: Optional[str] = None
    client_name: Optional[str] = None  # 'web', 'chrome-extension', 'android'
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class BookmarkTag:
    """Junction table linking bookmarks to tags."""
    bookmark_id: int = 0
    tag_id: int = 0


@dataclass
class InviteCode:
    """Invite code for authentication without OAuth.

    Used primarily for App Store reviewers and beta testers.
    """
    id: Optional[int] = None
    code: str = ""                      # 8-char alphanumeric (uppercase)
    user_id: int = 0                    # Account this grants access to
    created_at: Optional[str] = None
    expires_at: Optional[str] = None    # Default: 90 days from creation
    max_uses: Optional[int] = None      # None = unlimited
    use_count: int = 0
    is_revoked: bool = False
    note: Optional[str] = None          # e.g., "App Store reviewer"


def generate_invite_code(length: int = 8) -> str:
    """Generate random alphanumeric code (no ambiguous chars: 0,O,I,L,1)."""
    alphabet = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789'
    return ''.join(secrets.choice(alphabet) for _ in range(length))


# Helper functions for timestamp handling

def now_iso() -> str:
    """Return current UTC timestamp in ISO format."""
    return datetime.now(timezone.utc).replace(tzinfo=None).isoformat()


def future_iso(days: int = 0, hours: int = 0, minutes: int = 0, seconds: int = 0) -> str:
    """Return a future UTC timestamp in ISO format."""
    from datetime import timedelta
    dt = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
    return dt.isoformat()


def is_expired(timestamp: str) -> bool:
    """Check if an ISO timestamp is in the past."""
    if not timestamp:
        return True
    try:
        dt = datetime.fromisoformat(timestamp)
        return dt < datetime.now(timezone.utc).replace(tzinfo=None)
    except ValueError:
        return True
