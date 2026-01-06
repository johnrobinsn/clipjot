"""JSON API endpoints for ClipJot.

All endpoints use POST with JSON body and require API token authentication.
"""

import json
from typing import Optional
from dataclasses import asdict
from fasthtml.common import Response

from .models import Bookmark, Tag, now_iso
from . import db as database
from . import auth


# =============================================================================
# Error Response Helpers
# =============================================================================

def json_response(data: dict, status: int = 200) -> Response:
    """Create a JSON response."""
    return Response(
        json.dumps(data),
        status_code=status,
        media_type="application/json"
    )


def error_response(message: str, code: str, status: int = 400) -> Response:
    """Create an error JSON response."""
    return json_response({"error": message, "code": code}, status)


def invalid_token_error() -> Response:
    return error_response("Invalid or expired token", "INVALID_TOKEN", 401)


def permission_denied_error(message: str = "Permission denied") -> Response:
    return error_response(message, "PERMISSION_DENIED", 403)


def not_found_error(message: str = "Resource not found") -> Response:
    return error_response(message, "NOT_FOUND", 404)


def validation_error(message: str) -> Response:
    return error_response(message, "VALIDATION_ERROR", 400)


def rate_limited_error(retry_after: int) -> Response:
    response = error_response("Too many requests", "RATE_LIMITED", 429)
    response.headers["Retry-After"] = str(retry_after)
    return response


def limit_exceeded_error(message: str) -> Response:
    return error_response(message, "LIMIT_EXCEEDED", 403)


# =============================================================================
# API Authentication Middleware
# =============================================================================

def get_api_auth(request, db) -> tuple[Optional[auth.ApiToken], Optional[database.User], Optional[Response]]:
    """Extract and validate API token or session token from request.

    Accepts both API tokens and session tokens for Bearer auth.
    Session tokens get full read/write permissions.

    Returns (token, user, error_response) tuple.
    If error_response is not None, return it immediately.
    """
    # Get Authorization header
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None, None, invalid_token_error()

    token_str = auth_header[7:]  # Remove "Bearer " prefix
    if not token_str:
        return None, None, invalid_token_error()

    # Check rate limit
    allowed, retry_after = auth.check_rate_limit(auth.hash_token(token_str))
    if not allowed:
        return None, None, rate_limited_error(retry_after)

    # Try API token first
    result = auth.validate_api_token(db, token_str)
    if result:
        token, user = result
        return token, user, None

    # Fall back to session token (for extension/mobile apps)
    session_result = auth.validate_session(db, token_str)
    if session_result:
        session, user = session_result
        # Create a virtual ApiToken with full permissions for session-based auth
        virtual_token = auth.ApiToken(
            id=0,
            user_id=user.id,
            name="session",
            token_hash="",
            scope="write",  # "write" includes read permissions
            created_at=session.created_at,
            last_used_at=session.last_activity_at,
        )
        return virtual_token, user, None

    return None, None, invalid_token_error()


def require_scope(token: auth.ApiToken, scope: str) -> Optional[Response]:
    """Check if token has required scope. Returns error response if not."""
    if not auth.check_token_scope(token, scope):
        return permission_denied_error(f"Token requires '{scope}' scope")
    return None


# =============================================================================
# Bookmark API Endpoints
# =============================================================================

def api_bookmarks_add(request, db, data: dict) -> Response:
    """Add a new bookmark.

    POST /api/v1/bookmarks/add
    Requires: write scope

    Body:
        url: str (required)
        title: str (optional)
        comment: str (optional)
        tags: list[str] (optional) - tag names, created if not exist
        client_name: str (optional)
    """
    token, user, error = get_api_auth(request, db)
    if error:
        return error

    scope_error = require_scope(token, "write")
    if scope_error:
        return scope_error

    # Check bookmark limit
    allowed, current, max_count = auth.check_bookmark_limit(db, user)
    if not allowed:
        return limit_exceeded_error(f"Bookmark limit reached ({current}/{max_count})")

    # Validate required fields
    url = data.get("url", "").strip()
    if not url:
        return validation_error("url is required")

    # Create bookmark
    bookmark = Bookmark(
        user_id=user.id,
        url=url,
        title=data.get("title", "").strip() or None,
        comment=data.get("comment", "").strip() or None,
        client_name=data.get("client_name", "api"),
    )
    bookmark = database.create_bookmark(db, bookmark)

    # Handle tags
    tag_names = data.get("tags", [])
    tag_ids = []
    for name in tag_names:
        name = name.strip()
        if not name:
            continue
        tag = database.get_tag_by_name(db, user.id, name)
        if not tag:
            # Check tag limit before creating
            allowed, _, _ = auth.check_tag_limit(db, user)
            if allowed:
                tag = database.create_tag(db, user.id, name)
            else:
                continue  # Skip creating new tag if at limit
        if tag:
            tag_ids.append(tag.id)

    if tag_ids:
        database.set_bookmark_tags(db, bookmark.id, tag_ids)

    # Build response with tags
    tags = database.get_bookmark_tags(db, bookmark.id)
    result = {
        "id": bookmark.id,
        "url": bookmark.url,
        "title": bookmark.title,
        "comment": bookmark.comment,
        "tags": [{"id": t.id, "name": t.name} for t in tags],
        "client_name": bookmark.client_name,
        "created_at": bookmark.created_at,
    }

    return json_response(result, 201)


def api_bookmarks_edit(request, db, data: dict) -> Response:
    """Edit an existing bookmark.

    POST /api/v1/bookmarks/edit
    Requires: write scope

    Body:
        id: int (required)
        title: str (optional)
        comment: str (optional)
        tags: list[str] (optional)
    """
    token, user, error = get_api_auth(request, db)
    if error:
        return error

    scope_error = require_scope(token, "write")
    if scope_error:
        return scope_error

    bookmark_id = data.get("id")
    if not bookmark_id:
        return validation_error("id is required")

    bookmark = database.get_bookmark_by_id(db, bookmark_id)
    if not bookmark or bookmark.user_id != user.id:
        return not_found_error("Bookmark not found")

    # Update fields if provided
    if "title" in data:
        bookmark.title = data["title"].strip() or None
    if "comment" in data:
        bookmark.comment = data["comment"].strip() or None

    bookmark = database.update_bookmark(db, bookmark)

    # Update tags if provided
    if "tags" in data:
        tag_names = data["tags"]
        tag_ids = []
        for name in tag_names:
            name = name.strip()
            if not name:
                continue
            tag = database.get_tag_by_name(db, user.id, name)
            if not tag:
                allowed, _, _ = auth.check_tag_limit(db, user)
                if allowed:
                    tag = database.create_tag(db, user.id, name)
            if tag:
                tag_ids.append(tag.id)
        database.set_bookmark_tags(db, bookmark.id, tag_ids)

    # Build response
    tags = database.get_bookmark_tags(db, bookmark.id)
    result = {
        "id": bookmark.id,
        "url": bookmark.url,
        "title": bookmark.title,
        "comment": bookmark.comment,
        "tags": [{"id": t.id, "name": t.name} for t in tags],
        "client_name": bookmark.client_name,
        "created_at": bookmark.created_at,
        "updated_at": bookmark.updated_at,
    }

    return json_response(result)


def api_bookmarks_delete(request, db, data: dict) -> Response:
    """Delete a bookmark.

    POST /api/v1/bookmarks/delete
    Requires: write scope

    Body:
        id: int (required)
    """
    token, user, error = get_api_auth(request, db)
    if error:
        return error

    scope_error = require_scope(token, "write")
    if scope_error:
        return scope_error

    bookmark_id = data.get("id")
    if not bookmark_id:
        return validation_error("id is required")

    bookmark = database.get_bookmark_by_id(db, bookmark_id)
    if not bookmark or bookmark.user_id != user.id:
        return not_found_error("Bookmark not found")

    database.delete_bookmark(db, bookmark_id)

    return json_response({"deleted": True})


def api_bookmarks_search(request, db, data: dict) -> Response:
    """Search bookmarks.

    POST /api/v1/bookmarks/search
    Requires: read scope

    Body:
        query: str (optional) - search term
        tags: list[str] (optional) - filter by tag names
        page: int (optional, default 1)
        per_page: int (optional, default 50, max 100)
    """
    token, user, error = get_api_auth(request, db)
    if error:
        return error

    scope_error = require_scope(token, "read")
    if scope_error:
        return scope_error

    query = data.get("query", "").strip()
    page = max(1, data.get("page", 1))
    per_page = min(100, max(1, data.get("per_page", 50)))
    offset = (page - 1) * per_page

    # Search bookmarks
    bookmarks = database.search_bookmarks(db, user.id, query, per_page + 1, offset)

    # Check if there are more results
    has_more = len(bookmarks) > per_page
    if has_more:
        bookmarks = bookmarks[:per_page]

    # Filter by tags if specified
    filter_tags = data.get("tags", [])
    if filter_tags:
        filtered = []
        for b in bookmarks:
            tags = database.get_bookmark_tags(db, b.id)
            tag_names = {t.name for t in tags}
            if any(ft in tag_names for ft in filter_tags):
                filtered.append(b)
        bookmarks = filtered

    # Build response
    results = []
    for b in bookmarks:
        tags = database.get_bookmark_tags(db, b.id)
        results.append({
            "id": b.id,
            "url": b.url,
            "title": b.title,
            "comment": b.comment,
            "tags": [{"id": t.id, "name": t.name} for t in tags],
            "client_name": b.client_name,
            "created_at": b.created_at,
        })

    total = database.count_user_bookmarks(db, user.id)

    return json_response({
        "bookmarks": results,
        "total": total,
        "page": page,
        "per_page": per_page,
        "has_more": has_more,
    })


def api_bookmarks_list(request, db, data: dict) -> Response:
    """List bookmarks with cursor pagination.

    POST /api/v1/bookmarks/list
    Requires: read scope

    Body:
        cursor: str (optional) - opaque cursor for pagination
        limit: int (optional, default 100, max 500)
    """
    token, user, error = get_api_auth(request, db)
    if error:
        return error

    scope_error = require_scope(token, "read")
    if scope_error:
        return scope_error

    limit = min(500, max(1, data.get("limit", 100)))
    cursor = data.get("cursor")

    # Decode cursor (simple offset for now)
    offset = 0
    if cursor:
        try:
            import base64
            offset = int(base64.b64decode(cursor).decode())
        except Exception:
            offset = 0

    bookmarks = database.get_user_bookmarks(db, user.id, limit + 1, offset)

    has_more = len(bookmarks) > limit
    if has_more:
        bookmarks = bookmarks[:limit]

    # Build next cursor
    next_cursor = None
    if has_more:
        import base64
        next_cursor = base64.b64encode(str(offset + limit).encode()).decode()

    # Build response
    results = []
    for b in bookmarks:
        tags = database.get_bookmark_tags(db, b.id)
        results.append({
            "id": b.id,
            "url": b.url,
            "title": b.title,
            "comment": b.comment,
            "tags": [{"id": t.id, "name": t.name} for t in tags],
            "client_name": b.client_name,
            "created_at": b.created_at,
        })

    return json_response({
        "bookmarks": results,
        "has_more": has_more,
        "next_cursor": next_cursor,
    })


# =============================================================================
# Tag API Endpoints
# =============================================================================

def api_tags_list(request, db, data: dict) -> Response:
    """List user's tags with bookmark counts.

    POST /api/v1/tags/list
    Requires: read scope
    """
    token, user, error = get_api_auth(request, db)
    if error:
        return error

    scope_error = require_scope(token, "read")
    if scope_error:
        return scope_error

    tags = database.get_tags_with_counts(db, user.id)

    return json_response({"tags": tags})


def api_tags_create(request, db, data: dict) -> Response:
    """Create a new tag.

    POST /api/v1/tags/create
    Requires: write scope

    Body:
        name: str (required)
    """
    token, user, error = get_api_auth(request, db)
    if error:
        return error

    scope_error = require_scope(token, "write")
    if scope_error:
        return scope_error

    # Check tag limit
    allowed, current, max_count = auth.check_tag_limit(db, user)
    if not allowed:
        return limit_exceeded_error(f"Tag limit reached ({current}/{max_count})")

    name = data.get("name", "").strip()
    if not name:
        return validation_error("name is required")

    # Check if tag already exists
    existing = database.get_tag_by_name(db, user.id, name)
    if existing:
        return validation_error("Tag with this name already exists")

    tag = database.create_tag(db, user.id, name)

    return json_response({
        "id": tag.id,
        "name": tag.name,
        "created_at": tag.created_at,
    }, 201)


def api_tags_update(request, db, data: dict) -> Response:
    """Update a tag.

    POST /api/v1/tags/update
    Requires: write scope

    Body:
        id: int (required)
        name: str (optional)
    """
    token, user, error = get_api_auth(request, db)
    if error:
        return error

    scope_error = require_scope(token, "write")
    if scope_error:
        return scope_error

    tag_id = data.get("id")
    if not tag_id:
        return validation_error("id is required")

    tag = database.get_tag_by_id(db, tag_id)
    if not tag or tag.user_id != user.id:
        return not_found_error("Tag not found")

    if "name" in data:
        new_name = data["name"].strip()
        if new_name and new_name != tag.name:
            # Check for duplicate
            existing = database.get_tag_by_name(db, user.id, new_name)
            if existing:
                return validation_error("Tag with this name already exists")
            tag.name = new_name

    tag = database.update_tag(db, tag)

    return json_response({
        "id": tag.id,
        "name": tag.name,
        "created_at": tag.created_at,
    })


def api_tags_delete(request, db, data: dict) -> Response:
    """Delete a tag.

    POST /api/v1/tags/delete
    Requires: write scope

    Body:
        id: int (required)
    """
    token, user, error = get_api_auth(request, db)
    if error:
        return error

    scope_error = require_scope(token, "write")
    if scope_error:
        return scope_error

    tag_id = data.get("id")
    if not tag_id:
        return validation_error("id is required")

    tag = database.get_tag_by_id(db, tag_id)
    if not tag or tag.user_id != user.id:
        return not_found_error("Tag not found")

    database.delete_tag(db, tag_id)

    return json_response({"deleted": True})


# =============================================================================
# Export API Endpoint
# =============================================================================

def api_export(request, db, data: dict) -> Response:
    """Export all user's bookmarks as JSON.

    POST /api/v1/export
    Requires: read scope

    Body:
        format: str (optional, only "json" supported)
    """
    token, user, error = get_api_auth(request, db)
    if error:
        return error

    scope_error = require_scope(token, "read")
    if scope_error:
        return scope_error

    # Get all bookmarks
    bookmarks = []
    offset = 0
    while True:
        batch = database.get_user_bookmarks(db, user.id, 500, offset)
        if not batch:
            break
        for b in batch:
            tags = database.get_bookmark_tags(db, b.id)
            bookmarks.append({
                "url": b.url,
                "title": b.title,
                "comment": b.comment,
                "tags": [t.name for t in tags],
                "client_name": b.client_name,
                "created_at": b.created_at,
            })
        offset += 500
        if len(batch) < 500:
            break

    return json_response({
        "bookmarks": bookmarks,
        "exported_at": now_iso(),
        "count": len(bookmarks),
    })


# =============================================================================
# Import API Endpoint
# =============================================================================

def api_import(request, db, data: dict) -> Response:
    """Import bookmarks from JSON export format.

    POST /api/v1/import
    Requires: write scope

    Body:
        bookmarks: list[dict] (required) - list of bookmark objects
            Each bookmark: {url, title, comment, tags, client_name}
        mode: str (optional, default "merge")
            "merge" - add new bookmarks, skip duplicates by URL
            "replace" - delete all existing bookmarks first
    """
    token, user, error = get_api_auth(request, db)
    if error:
        return error

    scope_error = require_scope(token, "write")
    if scope_error:
        return scope_error

    bookmarks_data = data.get("bookmarks", [])
    if not bookmarks_data:
        return validation_error("bookmarks list is required")

    mode = data.get("mode", "merge")
    if mode not in ("merge", "replace"):
        return validation_error("mode must be 'merge' or 'replace'")

    # Get existing URLs for duplicate detection
    existing_urls = set()
    if mode == "merge":
        offset = 0
        while True:
            batch = database.get_user_bookmarks(db, user.id, 500, offset)
            if not batch:
                break
            for b in batch:
                existing_urls.add(b.url)
            offset += 500
            if len(batch) < 500:
                break

    # In replace mode, delete all existing bookmarks
    if mode == "replace":
        offset = 0
        while True:
            batch = database.get_user_bookmarks(db, user.id, 500, 0)
            if not batch:
                break
            for b in batch:
                database.delete_bookmark(db, b.id)

    imported = 0
    skipped = 0
    errors = []

    for i, bm_data in enumerate(bookmarks_data):
        url = bm_data.get("url", "").strip()
        if not url:
            errors.append(f"Bookmark {i}: missing url")
            continue

        # Skip duplicates in merge mode
        if mode == "merge" and url in existing_urls:
            skipped += 1
            continue

        # Check bookmark limit
        allowed, current, max_count = auth.check_bookmark_limit(db, user)
        if not allowed:
            errors.append(f"Bookmark limit reached ({current}/{max_count}). Stopped importing.")
            break

        # Create bookmark
        bookmark = Bookmark(
            user_id=user.id,
            url=url,
            title=bm_data.get("title", "").strip() or None,
            comment=bm_data.get("comment", "").strip() or None,
            client_name=bm_data.get("client_name", "import"),
        )
        bookmark = database.create_bookmark(db, bookmark)

        # Handle tags
        tag_names = bm_data.get("tags", [])
        tag_ids = []
        for name in tag_names:
            if isinstance(name, str):
                name = name.strip()
                if not name:
                    continue
                tag = database.get_tag_by_name(db, user.id, name)
                if not tag:
                    # Check tag limit before creating
                    allowed, _, _ = auth.check_tag_limit(db, user)
                    if allowed:
                        tag = database.create_tag(db, user.id, name)
                if tag:
                    tag_ids.append(tag.id)

        if tag_ids:
            database.set_bookmark_tags(db, bookmark.id, tag_ids)

        imported += 1
        existing_urls.add(url)  # Track to avoid duplicates within same import

    return json_response({
        "imported": imported,
        "skipped": skipped,
        "errors": errors if errors else None,
    }, 201 if imported > 0 else 200)
