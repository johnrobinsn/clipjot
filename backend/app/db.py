"""Database setup and query functions for LinkJot.

Uses FastLite for SQLite operations with dataclass models.
"""

from typing import Optional
from fastlite import database

from . import config
from .models import (
    User, Credential, Session, ApiToken, Tag, Bookmark, BookmarkTag,
    now_iso, is_expired
)


def _dict_to_dataclass(cls, data):
    """Convert a dict (from FastLite) to a dataclass instance."""
    if data is None:
        return None
    if isinstance(data, cls):
        return data
    if isinstance(data, dict):
        # Handle boolean conversion for SQLite (0/1 -> False/True)
        converted = {}
        for key, value in data.items():
            if key in ('is_premium', 'is_admin', 'is_suspended') and isinstance(value, int):
                converted[key] = bool(value)
            else:
                converted[key] = value
        return cls(**converted)
    return data

# Global database instance (initialized lazily)
_db = None


def get_db():
    """Get or create the database instance."""
    global _db
    if _db is None:
        _db = database(config.DATABASE_PATH)
        init_db(_db)
    return _db


def init_db(db=None):
    """Initialize database schema.

    Creates all tables if they don't exist. Safe to call multiple times.
    """
    if db is None:
        db = get_db()

    # Create tables from dataclasses
    db.create(User, pk='id')
    db.create(Credential, pk='id')
    db.create(Session, pk='id')
    db.create(ApiToken, pk='id')
    db.create(Tag, pk='id')
    db.create(Bookmark, pk='id')
    db.create(BookmarkTag, pk=['bookmark_id', 'tag_id'])

    # Create indexes for common queries
    _create_indexes(db)

    return db


def _create_indexes(db):
    """Create indexes for performance."""
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_bookmark_user_created ON bookmark(user_id, created_at DESC)",
        "CREATE INDEX IF NOT EXISTS idx_bookmark_user_url ON bookmark(user_id, url)",
        "CREATE INDEX IF NOT EXISTS idx_tag_user ON tag(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_session_expires ON session(expires_at)",
        "CREATE INDEX IF NOT EXISTS idx_session_user ON session(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_api_token_expires ON api_token(expires_at)",
        "CREATE INDEX IF NOT EXISTS idx_api_token_hash ON api_token(token_hash)",
        "CREATE INDEX IF NOT EXISTS idx_credential_provider ON credential(provider, provider_user_id)",
        "CREATE INDEX IF NOT EXISTS idx_bookmark_tag_bookmark ON bookmark_tag(bookmark_id)",
        "CREATE INDEX IF NOT EXISTS idx_bookmark_tag_tag ON bookmark_tag(tag_id)",
    ]
    for idx in indexes:
        try:
            db.execute(idx)
        except Exception:
            pass  # Index may already exist


# =============================================================================
# User queries
# =============================================================================

def get_user_by_id(db, user_id: int) -> Optional[User]:
    """Get user by ID."""
    try:
        result = db.t.user[user_id]
        return _dict_to_dataclass(User, result)
    except Exception:
        return None


def get_user_by_email(db, email: str) -> Optional[User]:
    """Get user by email."""
    users = list(db.t.user(where=f"email = '{email}'", limit=1))
    if not users:
        return None
    return _dict_to_dataclass(User, users[0])


def create_user(db, email: str) -> User:
    """Create a new user."""
    user = User(email=email, created_at=now_iso())
    result = db.t.user.insert(user)
    return _dict_to_dataclass(User, result)


def update_user(db, user: User) -> User:
    """Update an existing user."""
    result = db.t.user.update(user)
    return _dict_to_dataclass(User, result)


def delete_user(db, user_id: int) -> bool:
    """Delete a user and all their data (cascade)."""
    # Delete related data first (manual cascade since SQLite FKs might not be enforced)
    db.execute("DELETE FROM bookmark_tag WHERE bookmark_id IN (SELECT id FROM bookmark WHERE user_id = ?)", [user_id])
    db.execute("DELETE FROM bookmark WHERE user_id = ?", [user_id])
    db.execute("DELETE FROM tag WHERE user_id = ?", [user_id])
    db.execute("DELETE FROM session WHERE user_id = ?", [user_id])
    db.execute("DELETE FROM api_token WHERE user_id = ?", [user_id])
    db.execute("DELETE FROM credential WHERE user_id = ?", [user_id])
    db.t.user.delete(user_id)
    return True


# =============================================================================
# Credential queries
# =============================================================================

def get_credential(db, provider: str, provider_user_id: str) -> Optional[Credential]:
    """Get credential by provider and provider user ID."""
    creds = list(db.t.credential(
        where=f"provider = '{provider}' AND provider_user_id = '{provider_user_id}'",
        limit=1
    ))
    if not creds:
        return None
    return _dict_to_dataclass(Credential, creds[0])


def create_credential(db, user_id: int, provider: str, provider_user_id: str) -> Credential:
    """Create a new OAuth credential."""
    cred = Credential(
        user_id=user_id,
        provider=provider,
        provider_user_id=provider_user_id,
        created_at=now_iso()
    )
    result = db.t.credential.insert(cred)
    return _dict_to_dataclass(Credential, result)


# =============================================================================
# Session queries
# =============================================================================

def get_session(db, session_id: str) -> Optional[Session]:
    """Get session by ID, returning None if expired."""
    try:
        result = db.t.session[session_id]
        session = _dict_to_dataclass(Session, result)
        if is_expired(session.expires_at):
            delete_session(db, session_id)
            return None
        return session
    except Exception:
        return None


def get_user_sessions(db, user_id: int) -> list[Session]:
    """Get all active sessions for a user."""
    now = now_iso()
    sessions = list(db.t.session(where=f"user_id = {user_id} AND expires_at > '{now}'"))
    return [_dict_to_dataclass(Session, s) for s in sessions]


def create_session(db, session: Session) -> Session:
    """Create a new session."""
    if not session.created_at:
        session.created_at = now_iso()
    if not session.last_activity_at:
        session.last_activity_at = now_iso()
    result = db.t.session.insert(session)
    return _dict_to_dataclass(Session, result)


def update_session_activity(db, session_id: str):
    """Update last activity timestamp for a session."""
    db.execute(
        "UPDATE session SET last_activity_at = ? WHERE id = ?",
        [now_iso(), session_id]
    )


def delete_session(db, session_id: str):
    """Delete a session."""
    try:
        db.t.session.delete(session_id)
    except (KeyError, IndexError):
        pass


def delete_user_sessions(db, user_id: int, except_session: Optional[str] = None):
    """Delete all sessions for a user, optionally keeping one."""
    if except_session:
        db.execute(
            "DELETE FROM session WHERE user_id = ? AND id != ?",
            [user_id, except_session]
        )
    else:
        db.execute("DELETE FROM session WHERE user_id = ?", [user_id])


def cleanup_expired_sessions(db) -> int:
    """Delete all expired sessions. Returns count of deleted sessions."""
    now = now_iso()
    result = db.execute(f"SELECT COUNT(*) FROM session WHERE expires_at <= '{now}'")
    count = result.fetchone()[0]
    db.execute(f"DELETE FROM session WHERE expires_at <= '{now}'")
    return count


# =============================================================================
# API Token queries
# =============================================================================

def get_token_by_hash(db, token_hash: str) -> Optional[ApiToken]:
    """Get API token by hash."""
    tokens = list(db.t.api_token(where=f"token_hash = '{token_hash}'", limit=1))
    if not tokens:
        return None
    token = _dict_to_dataclass(ApiToken, tokens[0])
    if is_expired(token.expires_at):
        return None
    return token


def get_user_tokens(db, user_id: int) -> list[ApiToken]:
    """Get all API tokens for a user (excludes expired)."""
    now = now_iso()
    tokens = list(db.t.api_token(where=f"user_id = {user_id} AND expires_at > '{now}'"))
    return [_dict_to_dataclass(ApiToken, t) for t in tokens]


def create_token(db, token: ApiToken) -> ApiToken:
    """Create a new API token."""
    if not token.created_at:
        token.created_at = now_iso()
    result = db.t.api_token.insert(token)
    return _dict_to_dataclass(ApiToken, result)


def update_token_last_used(db, token_id: int):
    """Update last used timestamp for a token."""
    db.execute(
        "UPDATE api_token SET last_used_at = ? WHERE id = ?",
        [now_iso(), token_id]
    )


def get_token_by_id(db, token_id: int) -> Optional[ApiToken]:
    """Get a token by its ID."""
    try:
        result = db.t.api_token[token_id]
        if not result:
            return None
        # Result may already be an ApiToken or a dict-like object
        if isinstance(result, ApiToken):
            return result
        return ApiToken(**result)
    except (KeyError, IndexError):
        return None


def delete_token(db, token_id: int):
    """Delete an API token."""
    try:
        db.t.api_token.delete(token_id)
    except (KeyError, IndexError):
        pass


def cleanup_expired_tokens(db) -> int:
    """Delete all expired tokens. Returns count of deleted tokens."""
    now = now_iso()
    result = db.execute(f"SELECT COUNT(*) FROM api_token WHERE expires_at <= '{now}'")
    count = result.fetchone()[0]
    db.execute(f"DELETE FROM api_token WHERE expires_at <= '{now}'")
    return count


# =============================================================================
# Tag queries
# =============================================================================

def get_user_tags(db, user_id: int) -> list[Tag]:
    """Get all tags for a user."""
    tags = list(db.t.tag(where=f"user_id = {user_id}", order_by="name"))
    return [_dict_to_dataclass(Tag, t) for t in tags]


def get_tag_by_id(db, tag_id: int) -> Optional[Tag]:
    """Get tag by ID."""
    try:
        result = db.t.tag[tag_id]
        return _dict_to_dataclass(Tag, result)
    except Exception:
        return None


def get_tag_by_name(db, user_id: int, name: str) -> Optional[Tag]:
    """Get tag by user and name."""
    # Escape single quotes in name
    safe_name = name.replace("'", "''")
    tags = list(db.t.tag(where=f"user_id = {user_id} AND name = '{safe_name}'", limit=1))
    if not tags:
        return None
    return _dict_to_dataclass(Tag, tags[0])


def create_tag(db, user_id: int, name: str, color: str = "#6b7280") -> Tag:
    """Create a new tag."""
    tag = Tag(user_id=user_id, name=name, color=color, created_at=now_iso())
    result = db.t.tag.insert(tag)
    return _dict_to_dataclass(Tag, result)


def update_tag(db, tag: Tag) -> Tag:
    """Update an existing tag."""
    result = db.t.tag.update(tag)
    return _dict_to_dataclass(Tag, result)


def delete_tag(db, tag_id: int):
    """Delete a tag and remove it from all bookmarks (cascade)."""
    db.execute("DELETE FROM bookmark_tag WHERE tag_id = ?", [tag_id])
    db.t.tag.delete(tag_id)


def get_tag_bookmark_count(db, tag_id: int) -> int:
    """Get the number of bookmarks with a tag."""
    result = db.execute("SELECT COUNT(*) FROM bookmark_tag WHERE tag_id = ?", [tag_id])
    return result.fetchone()[0]


def get_tags_with_counts(db, user_id: int) -> list[dict]:
    """Get all tags for a user with bookmark counts."""
    result = db.execute("""
        SELECT t.id, t.name, t.color, t.created_at, COUNT(bt.bookmark_id) as bookmark_count
        FROM tag t
        LEFT JOIN bookmark_tag bt ON t.id = bt.tag_id
        WHERE t.user_id = ?
        GROUP BY t.id
        ORDER BY t.name
    """, [user_id])
    return [
        {"id": r[0], "name": r[1], "color": r[2], "created_at": r[3], "bookmark_count": r[4]}
        for r in result.fetchall()
    ]


# =============================================================================
# Bookmark queries
# =============================================================================

def get_bookmark_by_id(db, bookmark_id: int) -> Optional[Bookmark]:
    """Get bookmark by ID."""
    try:
        result = db.t.bookmark[bookmark_id]
        return _dict_to_dataclass(Bookmark, result)
    except Exception:
        return None


def get_user_bookmarks(db, user_id: int, limit: int = 50, offset: int = 0) -> list[Bookmark]:
    """Get bookmarks for a user, ordered by newest first."""
    bookmarks = list(db.t.bookmark(
        where=f"user_id = {user_id}",
        order_by="created_at DESC",
        limit=limit,
        offset=offset
    ))
    return [_dict_to_dataclass(Bookmark, b) for b in bookmarks]


def search_bookmarks(db, user_id: int, query: str, limit: int = 50, offset: int = 0) -> list[Bookmark]:
    """Search bookmarks using LIKE with wildcards.

    Searches in title, url, and comment fields.
    """
    if not query or not query.strip():
        return get_user_bookmarks(db, user_id, limit, offset)

    # Escape special characters and add wildcards
    safe_query = query.replace("'", "''").replace("%", "\\%").replace("_", "\\_")
    pattern = f"%{safe_query}%"

    result = db.execute("""
        SELECT id, user_id, url, title, comment, client_name, created_at, updated_at
        FROM bookmark
        WHERE user_id = ?
        AND (title LIKE ? ESCAPE '\\' OR url LIKE ? ESCAPE '\\' OR comment LIKE ? ESCAPE '\\')
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
    """, [user_id, pattern, pattern, pattern, limit, offset])

    # Convert to Bookmark objects
    return [Bookmark(id=row[0], user_id=row[1], url=row[2], title=row[3],
                     comment=row[4], client_name=row[5], created_at=row[6], updated_at=row[7])
            for row in result.fetchall()]


def count_user_bookmarks(db, user_id: int) -> int:
    """Count total bookmarks for a user."""
    result = db.execute("SELECT COUNT(*) FROM bookmark WHERE user_id = ?", [user_id])
    return result.fetchone()[0]


def create_bookmark(db, bookmark: Bookmark) -> Bookmark:
    """Create a new bookmark."""
    if not bookmark.created_at:
        bookmark.created_at = now_iso()
    if not bookmark.updated_at:
        bookmark.updated_at = bookmark.created_at
    result = db.t.bookmark.insert(bookmark)
    return _dict_to_dataclass(Bookmark, result)


def update_bookmark(db, bookmark: Bookmark) -> Bookmark:
    """Update an existing bookmark."""
    bookmark.updated_at = now_iso()
    result = db.t.bookmark.update(bookmark)
    return _dict_to_dataclass(Bookmark, result)


def delete_bookmark(db, bookmark_id: int):
    """Delete a bookmark and its tag associations."""
    db.execute("DELETE FROM bookmark_tag WHERE bookmark_id = ?", [bookmark_id])
    db.t.bookmark.delete(bookmark_id)


# =============================================================================
# Bookmark-Tag relationship queries
# =============================================================================

def get_bookmark_tags(db, bookmark_id: int) -> list[Tag]:
    """Get all tags for a bookmark."""
    result = db.execute("""
        SELECT t.id, t.user_id, t.name, t.color, t.created_at FROM tag t
        JOIN bookmark_tag bt ON t.id = bt.tag_id
        WHERE bt.bookmark_id = ?
        ORDER BY t.name
    """, [bookmark_id])
    return [Tag(id=row[0], user_id=row[1], name=row[2], color=row[3], created_at=row[4])
            for row in result.fetchall()]


def set_bookmark_tags(db, bookmark_id: int, tag_ids: list[int]):
    """Set the tags for a bookmark (replaces existing tags)."""
    db.execute("DELETE FROM bookmark_tag WHERE bookmark_id = ?", [bookmark_id])
    for tag_id in tag_ids:
        db.t.bookmark_tag.insert(BookmarkTag(bookmark_id=bookmark_id, tag_id=tag_id))


def add_bookmark_tag(db, bookmark_id: int, tag_id: int):
    """Add a tag to a bookmark."""
    try:
        db.t.bookmark_tag.insert(BookmarkTag(bookmark_id=bookmark_id, tag_id=tag_id))
    except Exception:
        pass  # Already exists


def remove_bookmark_tag(db, bookmark_id: int, tag_id: int):
    """Remove a tag from a bookmark."""
    db.execute(
        "DELETE FROM bookmark_tag WHERE bookmark_id = ? AND tag_id = ?",
        [bookmark_id, tag_id]
    )


# =============================================================================
# Admin/Stats queries
# =============================================================================

def get_all_users(db, limit: int = 100, offset: int = 0) -> list[User]:
    """Get all users (for admin)."""
    users = list(db.t.user(order_by="created_at DESC", limit=limit, offset=offset))
    return [_dict_to_dataclass(User, u) for u in users]


def count_all_users(db) -> int:
    """Count total users."""
    result = db.execute("SELECT COUNT(*) FROM user")
    return result.fetchone()[0]


def count_all_bookmarks(db) -> int:
    """Count total bookmarks across all users."""
    result = db.execute("SELECT COUNT(*) FROM bookmark")
    return result.fetchone()[0]


def count_active_sessions(db) -> int:
    """Count active (non-expired) sessions."""
    now = now_iso()
    result = db.execute(f"SELECT COUNT(*) FROM session WHERE expires_at > '{now}'")
    return result.fetchone()[0]


def get_user_stats(db, user_id: int) -> dict:
    """Get statistics for a user (for admin view)."""
    bookmark_count = count_user_bookmarks(db, user_id)
    tag_count = db.execute("SELECT COUNT(*) FROM tag WHERE user_id = ?", [user_id]).fetchone()[0]
    session_count = len(get_user_sessions(db, user_id))
    token_count = len(get_user_tokens(db, user_id))

    return {
        "bookmark_count": bookmark_count,
        "tag_count": tag_count,
        "session_count": session_count,
        "token_count": token_count,
    }
