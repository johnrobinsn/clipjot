"""Authentication handlers for ClipJot.

Implements OAuth authentication with Google and GitHub using FastHTML's OAuth support.
"""

import secrets
import hashlib
from typing import Optional
from fasthtml.common import RedirectResponse

from . import config
from .models import User, Session, ApiToken, future_iso, now_iso, is_expired
from . import db as database


# =============================================================================
# Session Management
# =============================================================================

def generate_session_token() -> str:
    """Generate a cryptographically secure session token."""
    return secrets.token_urlsafe(32)


def generate_api_token() -> str:
    """Generate a cryptographically secure API token."""
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """Hash a token using SHA-256."""
    return hashlib.sha256(token.encode()).hexdigest()


def create_user_session(
    db,
    user_id: int,
    user_agent: Optional[str] = None,
    client_name: str = "web",
    ip_address: Optional[str] = None
) -> tuple[str, Session]:
    """Create a new session for a user.

    Returns (token, session) tuple. The token is only returned once.
    """
    token = generate_session_token()
    session = Session(
        id=token,
        user_id=user_id,
        expires_at=future_iso(seconds=config.SESSION_MAX_AGE),
        user_agent=user_agent,
        client_name=client_name,
        ip_address=ip_address,
    )
    database.create_session(db, session)
    return token, session


def validate_session(db, session_token: str) -> Optional[tuple[Session, User]]:
    """Validate a session token and return session and user if valid.

    Returns None if session is invalid or expired.
    Updates last_activity_at on valid session.
    """
    session = database.get_session(db, session_token)
    if not session:
        return None

    user = database.get_user_by_id(db, session.user_id)
    if not user:
        database.delete_session(db, session_token)
        return None

    if user.is_suspended:
        return None

    # Update activity
    database.update_session_activity(db, session_token)

    return session, user


def logout_session(db, session_token: str):
    """Log out a session."""
    database.delete_session(db, session_token)


# =============================================================================
# API Token Management
# =============================================================================

def create_api_token(
    db,
    user_id: int,
    name: str,
    scope: str = "read",
    expires_days: int = 365
) -> tuple[str, ApiToken]:
    """Create a new API token for a user.

    Returns (plaintext_token, token_record) tuple.
    The plaintext token is only returned once and should be shown to the user.
    """
    plaintext = generate_api_token()
    token = ApiToken(
        user_id=user_id,
        name=name,
        token_hash=hash_token(plaintext),
        scope=scope,
        expires_at=future_iso(days=expires_days),
    )
    token = database.create_token(db, token)
    return plaintext, token


def validate_api_token(db, plaintext_token: str) -> Optional[tuple[ApiToken, User]]:
    """Validate an API token and return token and user if valid.

    Returns None if token is invalid or expired.
    Updates last_used_at on valid token.
    """
    token_hash = hash_token(plaintext_token)
    token = database.get_token_by_hash(db, token_hash)
    if not token:
        return None

    user = database.get_user_by_id(db, token.user_id)
    if not user:
        return None

    if user.is_suspended:
        return None

    # Update last used
    database.update_token_last_used(db, token.id)

    return token, user


def check_token_scope(token: ApiToken, required_scope: str) -> bool:
    """Check if a token has the required scope.

    'write' scope includes 'read' permissions.
    """
    if required_scope == "read":
        return token.scope in ("read", "write")
    return token.scope == required_scope


# =============================================================================
# OAuth Handlers
# =============================================================================

def get_or_create_oauth_user(db, provider: str, provider_user_id: str, email: str) -> User:
    """Get existing user or create new one from OAuth login.

    Each provider creates a separate user account (no email linking).
    """
    # Check if credential already exists
    credential = database.get_credential(db, provider, provider_user_id)
    if credential:
        user = database.get_user_by_id(db, credential.user_id)
        if user:
            return user
        # Credential exists but user doesn't - clean up and create new
        # This shouldn't happen normally

    # Create new user
    user = database.create_user(db, email)

    # Create credential linking
    database.create_credential(db, user.id, provider, provider_user_id)

    return user


class ClipJotAuth:
    """OAuth authentication handler for ClipJot.

    Handles Google and GitHub OAuth flows.
    """

    def __init__(self, db_getter):
        """Initialize with a function that returns the database."""
        self.db_getter = db_getter

    @property
    def db(self):
        return self.db_getter()

    def handle_oauth_callback(
        self,
        provider: str,
        user_info: dict,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
        client_name: str = "web",
    ) -> tuple[str, User]:
        """Handle OAuth callback after successful authentication.

        Args:
            provider: OAuth provider name ('google' or 'github')
            user_info: User information from OAuth provider
            user_agent: Request user agent
            ip_address: Request IP address
            client_name: Client identifier ('web', 'chrome-extension', 'android')

        Returns:
            (session_token, user) tuple
        """
        # Extract user info based on provider
        if provider == "google":
            provider_user_id = user_info.get("sub", user_info.get("id"))
            email = user_info.get("email", "")
        elif provider == "github":
            provider_user_id = str(user_info.get("id"))
            email = user_info.get("email") or f"{user_info.get('login')}@github.local"
        else:
            raise ValueError(f"Unknown provider: {provider}")

        # Get or create user
        user = get_or_create_oauth_user(self.db, provider, provider_user_id, email)

        # Check if suspended
        if user.is_suspended:
            raise PermissionError("User account is suspended")

        # Create session
        token, session = create_user_session(
            self.db,
            user.id,
            user_agent=user_agent,
            client_name=client_name,
            ip_address=ip_address,
        )

        return token, user


# =============================================================================
# Rate Limiting (simple in-memory implementation)
# =============================================================================

_rate_limit_store: dict[str, list[float]] = {}


def check_rate_limit(identifier: str) -> tuple[bool, int]:
    """Check if request is within rate limit.

    Args:
        identifier: Unique identifier (e.g., token hash or IP)

    Returns:
        (allowed, retry_after_seconds) tuple
    """
    import time

    now = time.time()
    window = config.RATE_LIMIT_WINDOW
    max_requests = config.RATE_LIMIT_REQUESTS

    # Get or create request log
    if identifier not in _rate_limit_store:
        _rate_limit_store[identifier] = []

    # Remove old entries
    _rate_limit_store[identifier] = [
        ts for ts in _rate_limit_store[identifier]
        if now - ts < window
    ]

    # Check limit
    if len(_rate_limit_store[identifier]) >= max_requests:
        oldest = min(_rate_limit_store[identifier])
        retry_after = int(oldest + window - now) + 1
        return False, retry_after

    # Record request
    _rate_limit_store[identifier].append(now)
    return True, 0


def clear_rate_limit_store():
    """Clear rate limit store (for testing)."""
    global _rate_limit_store
    _rate_limit_store = {}


# =============================================================================
# Free Tier Limit Checking
# =============================================================================

def check_bookmark_limit(db, user: User) -> tuple[bool, int, int]:
    """Check if user can add more bookmarks.

    Returns (allowed, current_count, max_count) tuple.
    Premium users have no limit.
    """
    if user.is_premium:
        return True, 0, -1  # -1 means unlimited

    current = database.count_user_bookmarks(db, user.id)
    max_allowed = config.FREE_TIER_MAX_BOOKMARKS

    return current < max_allowed, current, max_allowed


def check_tag_limit(db, user: User) -> tuple[bool, int, int]:
    """Check if user can add more tags.

    Returns (allowed, current_count, max_count) tuple.
    Premium users have no limit.
    """
    if user.is_premium:
        return True, 0, -1  # -1 means unlimited

    tags = database.get_user_tags(db, user.id)
    current = len(tags)
    max_allowed = config.FREE_TIER_MAX_TAGS

    return current < max_allowed, current, max_allowed
