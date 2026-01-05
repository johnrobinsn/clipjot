"""Web UI views for LinkJot.

Handles all HTML routes for the web interface.
"""

import json
from typing import Optional
from fasthtml.common import *

from . import config
from . import db as database
from . import auth
from .models import Bookmark, Tag, User, now_iso
from .components import (
    page_layout, bookmark_list, bookmark_form, bookmark_row,
    tag_list_item, tag_chip, pagination, modal, modal_container,
    bulk_actions_bar, flash_message,
)


# =============================================================================
# View Helpers
# =============================================================================

def get_current_user(request, db) -> Optional[tuple[User, str]]:
    """Get current user from session cookie.

    Returns (user, session_token) or None if not authenticated.
    """
    session_token = request.cookies.get("session")
    if not session_token:
        return None

    result = auth.validate_session(db, session_token)
    if not result:
        return None

    session, user = result
    return user, session_token


def require_auth(request, db):
    """Require authentication, redirect to login if not authenticated.

    Returns (user, session_token) or raises RedirectResponse.
    """
    result = get_current_user(request, db)
    if not result:
        return RedirectResponse("/login", status_code=303)
    return result


def set_session_cookie(response, token: str):
    """Set session cookie on response."""
    response.set_cookie(
        "session",
        token,
        max_age=config.SESSION_MAX_AGE,
        httponly=True,
        samesite="lax",  # Use lax for OAuth redirect compatibility
        secure=config.BASE_URL.startswith("https"),
        path="/",  # Ensure cookie is available site-wide
    )
    return response


def clear_session_cookie(response):
    """Clear session cookie."""
    response.delete_cookie("session", path="/")
    return response


# =============================================================================
# Public Routes
# =============================================================================

def login_page(request, db):
    """Login page with OAuth provider selection.

    GET /login
    """
    # If already logged in, redirect to home
    if get_current_user(request, db):
        return RedirectResponse("/", status_code=303)

    providers = []
    if config.has_google_oauth():
        providers.append(
            A(
                "Continue with Google",
                href="/auth/google",
                cls="btn btn-outline w-full mb-3",
            )
        )
    if config.has_github_oauth():
        providers.append(
            A(
                "Continue with GitHub",
                href="/auth/github",
                cls="btn btn-outline w-full mb-3",
            )
        )

    if not providers:
        providers.append(
            P("No OAuth providers configured. Please set up Google or GitHub OAuth.",
              cls="text-error")
        )

    content = Div(
        Div(
            Div(
                H2("Welcome to LinkJot", cls="card-title mb-6"),
                P("Sign in to manage your bookmarks", cls="mb-6 text-base-content/70"),
                *providers,
                cls="card-body items-center text-center",
            ),
            cls="card w-96 bg-base-100 shadow-xl",
        ),
        cls="flex items-center justify-center min-h-[60vh]",
    )

    return page_layout(content, title="Login - LinkJot")


def health_check(request, db):
    """Health check endpoint.

    GET /health
    """
    return Response(
        json.dumps({"status": "ok"}),
        media_type="application/json",
    )


# =============================================================================
# OAuth Routes (to be connected in main.py with actual OAuth clients)
# =============================================================================

def oauth_callback_handler(request, db, provider: str, user_info: dict):
    """Handle OAuth callback after successful authentication.

    Called by OAuth client callbacks.
    """
    auth_handler = auth.LinkJotAuth(lambda: db)

    try:
        token, user = auth_handler.handle_oauth_callback(
            provider=provider,
            user_info=user_info,
            user_agent=request.headers.get("user-agent"),
            ip_address=request.client.host if request.client else None,
        )
    except PermissionError as e:
        # User is suspended
        content = Div(
            P(str(e)),
            cls="alert alert-error",
        )
        return page_layout(content, title="Access Denied - LinkJot")

    # Create response with session cookie
    response = RedirectResponse("/", status_code=303)
    return set_session_cookie(response, token)


def logout(request, db):
    """Log out current user.

    POST /logout
    """
    result = get_current_user(request, db)
    if result:
        user, session_token = result
        auth.logout_session(db, session_token)

    # Use HX-Redirect for HTMX compatibility
    response = Response(status_code=200)
    response.headers["HX-Redirect"] = "/login"
    return clear_session_cookie(response)


# =============================================================================
# Bookmark Routes
# =============================================================================

def bookmark_index(request, db):
    """Main bookmark list page.

    GET /
    """
    result = require_auth(request, db)
    if isinstance(result, Response):
        return result
    user, _ = result

    # Get query params
    query = request.query_params.get("q", "").strip()
    page = int(request.query_params.get("page", 1))
    per_page = 50

    # Search or list bookmarks
    if query:
        bookmarks = database.search_bookmarks(db, user.id, query, per_page, (page - 1) * per_page)
    else:
        bookmarks = database.get_user_bookmarks(db, user.id, per_page, (page - 1) * per_page)

    total = database.count_user_bookmarks(db, user.id)

    # Get tags for each bookmark
    bookmark_data = []
    for b in bookmarks:
        tags = database.get_bookmark_tags(db, b.id)
        bookmark_data.append((b, tags))

    # Get all tags for filter dropdown
    all_tags = database.get_user_tags(db, user.id)

    # Build search info
    search_info_items = []
    if query:
        search_info_items.append(P(f'Showing results for "{query}"', cls="text-sm text-base-content/70"))
    search_info_items.append(P(f"{total} bookmarks total", cls="text-sm text-base-content/70"))

    # Build bookmark list or empty state
    if bookmark_data:
        bookmark_section = bookmark_list(bookmark_data)
    else:
        bookmark_section = Div(
            P("No bookmarks yet", cls="text-xl mb-4"),
            P("Add your first bookmark to get started!", cls="text-base-content/70"),
            cls="text-center py-12",
        )

    # Build content
    content = Div(
        # Header
        Div(
            H1("My Bookmarks", cls="text-2xl font-bold"),
            Button(
                "+ Add Bookmark",
                cls="btn btn-primary",
                hx_get="/bookmarks/add",
                hx_target="#modal-container",
            ),
            cls="flex justify-between items-center mb-6",
        ),
        # Search info
        Div(*search_info_items, cls="mb-4"),
        # Bulk actions bar
        bulk_actions_bar(),
        # Bookmark list
        bookmark_section,
        # Pagination
        pagination(page, total, per_page, f"/?q={query}" if query else "/"),
        # Modal container
        modal_container(),
    )

    return page_layout(content, title="My Bookmarks - LinkJot", user=user)


def bookmark_add_form(request, db):
    """Show add bookmark form modal.

    GET /bookmarks/add
    """
    result = require_auth(request, db)
    if isinstance(result, Response):
        return result
    user, _ = result

    all_tags = database.get_user_tags(db, user.id)
    form = bookmark_form(all_tags=all_tags)

    return modal("Add Bookmark", form)


async def bookmark_add(request, db):
    """Add a new bookmark.

    POST /bookmarks/add
    """
    result = require_auth(request, db)
    if isinstance(result, Response):
        return result
    user, _ = result

    # Get form data
    form = await request.form()
    url = form.get("url", "").strip()
    title = form.get("title", "").strip()
    comment = form.get("comment", "").strip()
    tag_ids = form.getlist("tags")

    if not url:
        return Response("URL is required", status_code=400)

    # Check limit
    allowed, current, max_count = auth.check_bookmark_limit(db, user)
    if not allowed:
        return Response(f"Bookmark limit reached ({current}/{max_count})", status_code=403)

    # Create bookmark
    bookmark = Bookmark(
        user_id=user.id,
        url=url,
        title=title or None,
        comment=comment or None,
        client_name="web",
    )
    bookmark = database.create_bookmark(db, bookmark)

    # Set tags
    if tag_ids:
        database.set_bookmark_tags(db, bookmark.id, [int(t) for t in tag_ids])

    # Return redirect with HX-Redirect header for HTMX
    response = Response(status_code=200)
    response.headers["HX-Redirect"] = "/"
    return response


def bookmark_edit_form(request, db, bookmark_id: int):
    """Show edit bookmark form modal.

    GET /bookmarks/{id}/edit
    """
    result = require_auth(request, db)
    if isinstance(result, Response):
        return result
    user, _ = result

    bookmark = database.get_bookmark_by_id(db, bookmark_id)
    if not bookmark or bookmark.user_id != user.id:
        return Response("Not found", status_code=404)

    tags = database.get_bookmark_tags(db, bookmark.id)
    all_tags = database.get_user_tags(db, user.id)
    form = bookmark_form(bookmark=bookmark, tags=tags, all_tags=all_tags)

    return modal("Edit Bookmark", form)


async def bookmark_edit(request, db, bookmark_id: int):
    """Update a bookmark.

    POST /bookmarks/{id}
    """
    result = require_auth(request, db)
    if isinstance(result, Response):
        return result
    user, _ = result

    bookmark = database.get_bookmark_by_id(db, bookmark_id)
    if not bookmark or bookmark.user_id != user.id:
        return Response("Not found", status_code=404)

    # Get form data
    form = await request.form()
    bookmark.title = form.get("title", "").strip() or None
    bookmark.comment = form.get("comment", "").strip() or None
    tag_ids = form.getlist("tags")

    bookmark = database.update_bookmark(db, bookmark)

    # Update tags
    database.set_bookmark_tags(db, bookmark.id, [int(t) for t in tag_ids])

    # Return updated row
    tags = database.get_bookmark_tags(db, bookmark.id)
    return bookmark_row(bookmark, tags)


def bookmark_delete(request, db, bookmark_id: int):
    """Delete a bookmark.

    DELETE /bookmarks/{id}
    """
    result = require_auth(request, db)
    if isinstance(result, Response):
        return result
    user, _ = result

    bookmark = database.get_bookmark_by_id(db, bookmark_id)
    if not bookmark or bookmark.user_id != user.id:
        return Response("Not found", status_code=404)

    database.delete_bookmark(db, bookmark_id)

    # Return empty for HTMX to remove the row
    return Response("")


async def bookmark_bulk_delete(request, db):
    """Delete multiple bookmarks.

    DELETE /bookmarks/bulk
    """
    result = require_auth(request, db)
    if isinstance(result, Response):
        return result
    user, _ = result

    form = await request.form()
    ids = form.getlist("selected")

    for id_str in ids:
        bookmark = database.get_bookmark_by_id(db, int(id_str))
        if bookmark and bookmark.user_id == user.id:
            database.delete_bookmark(db, bookmark.id)

    response = Response(status_code=200)
    response.headers["HX-Redirect"] = "/"
    return response


# =============================================================================
# Settings Routes
# =============================================================================

def settings_page(request, db):
    """User settings overview.

    GET /settings
    """
    result = require_auth(request, db)
    if isinstance(result, Response):
        return result
    user, _ = result

    stats = database.get_user_stats(db, user.id)

    content = Div(
        H1("Settings", cls="text-2xl font-bold mb-6"),
        # Profile card
        Div(
            Div(
                H2("Profile", cls="card-title"),
                P(f"Email: {user.email}"),
                P(f"Account type: {'Premium' if user.is_premium else 'Free'}"),
                P(f"Member since: {user.created_at[:10] if user.created_at else 'Unknown'}"),
                cls="card-body",
            ),
            cls="card bg-base-100 shadow-xl mb-6",
        ),
        # Stats card
        Div(
            Div(
                H2("Usage", cls="card-title"),
                Div(
                    Div(
                        Div("Bookmarks", cls="stat-title"),
                        Div(str(stats["bookmark_count"]), cls="stat-value"),
                        Div(
                            f"of {config.FREE_TIER_MAX_BOOKMARKS}" if not user.is_premium else "unlimited",
                            cls="stat-desc"
                        ),
                        cls="stat",
                    ),
                    Div(
                        Div("Tags", cls="stat-title"),
                        Div(str(stats["tag_count"]), cls="stat-value"),
                        Div(
                            f"of {config.FREE_TIER_MAX_TAGS}" if not user.is_premium else "unlimited",
                            cls="stat-desc"
                        ),
                        cls="stat",
                    ),
                    Div(
                        Div("Active Sessions", cls="stat-title"),
                        Div(str(stats["session_count"]), cls="stat-value"),
                        cls="stat",
                    ),
                    cls="stats stats-vertical lg:stats-horizontal shadow",
                ),
                cls="card-body",
            ),
            cls="card bg-base-100 shadow-xl mb-6",
        ),
        # Links to other settings
        Div(
            A("Manage Tags", href="/settings/tags", cls="btn btn-outline"),
            A("API Tokens", href="/settings/tokens", cls="btn btn-outline"),
            A("Sessions", href="/settings/sessions", cls="btn btn-outline"),
            A("Export Data", href="/export", cls="btn btn-outline"),
            cls="flex flex-wrap gap-4",
        ),
    )

    return page_layout(content, title="Settings - LinkJot", user=user)


def settings_tags(request, db):
    """Tag management page.

    GET /settings/tags
    """
    result = require_auth(request, db)
    if isinstance(result, Response):
        return result
    user, _ = result

    tags = database.get_tags_with_counts(db, user.id)

    if tags:
        tag_rows = [tag_list_item(t) for t in tags]
        tag_section = Table(
            Thead(
                Tr(
                    Th("Tag"),
                    Th("Bookmarks"),
                    Th("Actions"),
                )
            ),
            Tbody(*tag_rows, id="tag-list"),
            cls="table w-full",
        )
    else:
        tag_section = P("No tags yet. Create one to organize your bookmarks!")

    content = Div(
        Div(
            H1("Manage Tags", cls="text-2xl font-bold"),
            Button(
                "+ New Tag",
                cls="btn btn-primary",
                hx_get="/settings/tags/add",
                hx_target="#modal-container",
            ),
            cls="flex justify-between items-center mb-6",
        ),
        tag_section,
        modal_container(),
    )

    return page_layout(content, title="Manage Tags - LinkJot", user=user)


def settings_tag_add_form(request, db):
    """Show add tag form modal.

    GET /settings/tags/add
    """
    result = require_auth(request, db)
    if isinstance(result, Response):
        return result

    form = Form(
        Div(
            Label("Name", cls="label"),
            Input(type="text", name="name", required=True, cls="input input-bordered"),
            cls="form-control",
        ),
        Div(
            Label("Color", cls="label"),
            Input(type="color", name="color", value="#6b7280", cls="w-20 h-10"),
            cls="form-control",
        ),
        Div(
            Button("Cancel", type="button", cls="btn btn-ghost", onclick="closeModal()"),
            Button("Create Tag", type="submit", cls="btn btn-primary"),
            cls="flex justify-end gap-2",
        ),
        cls="space-y-4",
        action="/settings/tags/add",
        method="post",
        hx_post="/settings/tags/add",
    )

    return modal("New Tag", form)


async def settings_tag_add(request, db):
    """Create a new tag.

    POST /settings/tags/add
    """
    result = require_auth(request, db)
    if isinstance(result, Response):
        return result
    user, _ = result

    form = await request.form()
    name = form.get("name", "").strip()
    color = form.get("color", "#6b7280").strip()

    if not name:
        return Response("Name is required", status_code=400)

    # Check limit
    allowed, _, _ = auth.check_tag_limit(db, user)
    if not allowed:
        return Response("Tag limit reached", status_code=403)

    # Check duplicate
    if database.get_tag_by_name(db, user.id, name):
        return Response("Tag already exists", status_code=400)

    database.create_tag(db, user.id, name, color)

    response = Response(status_code=200)
    response.headers["HX-Redirect"] = "/settings/tags"
    return response


def settings_tag_delete(request, db, tag_id: int):
    """Delete a tag.

    DELETE /settings/tags/{id}
    """
    result = require_auth(request, db)
    if isinstance(result, Response):
        return result
    user, _ = result

    tag = database.get_tag_by_id(db, tag_id)
    if not tag or tag.user_id != user.id:
        return Response("Not found", status_code=404)

    database.delete_tag(db, tag_id)

    return Response("")


def settings_tokens(request, db):
    """API token management page.

    GET /settings/tokens
    """
    result = require_auth(request, db)
    if isinstance(result, Response):
        return result
    user, _ = result

    tokens = database.get_user_tokens(db, user.id)

    if tokens:
        token_rows = [
            Tr(
                Td(t.name),
                Td(Span(t.scope, cls=f"badge {'badge-success' if t.scope == 'write' else 'badge-info'}")),
                Td(t.created_at[:10] if t.created_at else ""),
                Td(t.expires_at[:10] if t.expires_at else ""),
                Td(t.last_used_at[:10] if t.last_used_at else "Never"),
                Td(
                    Button(
                        "Revoke",
                        cls="btn btn-xs btn-error",
                        hx_delete=f"/settings/tokens/{t.id}",
                        hx_confirm="Revoke this token?",
                        hx_target=f"#token-{t.id}",
                        hx_swap="outerHTML",
                    )
                ),
                id=f"token-{t.id}",
            )
            for t in tokens
        ]
        token_section = Table(
            Thead(
                Tr(
                    Th("Name"),
                    Th("Scope"),
                    Th("Created"),
                    Th("Expires"),
                    Th("Last Used"),
                    Th("Actions"),
                )
            ),
            Tbody(*token_rows),
            cls="table w-full",
        )
    else:
        token_section = P("No API tokens yet.")

    content = Div(
        Div(
            H1("API Tokens", cls="text-2xl font-bold"),
            Button(
                "+ New Token",
                cls="btn btn-primary",
                hx_get="/settings/tokens/create",
                hx_target="#modal-container",
            ),
            cls="flex justify-between items-center mb-6",
        ),
        token_section,
        modal_container(),
    )

    return page_layout(content, title="API Tokens - LinkJot", user=user)


def settings_sessions(request, db):
    """Session management page.

    GET /settings/sessions
    """
    result = require_auth(request, db)
    if isinstance(result, Response):
        return result
    user, current_token = result

    sessions = database.get_user_sessions(db, user.id)

    def session_row(s):
        user_agent_display = s.user_agent[:50] + "..." if s.user_agent and len(s.user_agent) > 50 else (s.user_agent or "Unknown")
        device_cell_children = [Div(user_agent_display, title=s.user_agent)]
        if s.id == current_token:
            device_cell_children.append(Span(" (current)", cls="badge badge-success ml-2"))

        if s.id != current_token:
            action_cell = Button(
                "Revoke",
                cls="btn btn-xs btn-error",
                hx_post=f"/settings/sessions/{s.id}/revoke",
                hx_target=f"#session-{s.id[:8]}",
                hx_swap="outerHTML",
            )
        else:
            action_cell = Span("Current", cls="text-sm text-base-content/50")

        return Tr(
            Td(*device_cell_children),
            Td(s.client_name or "web"),
            Td(s.ip_address or "Unknown"),
            Td(s.last_activity_at[:16] if s.last_activity_at else ""),
            Td(action_cell),
            id=f"session-{s.id[:8]}",
        )

    session_rows = [session_row(s) for s in sessions]

    content = Div(
        Div(
            H1("Active Sessions", cls="text-2xl font-bold"),
            Button(
                "Revoke All Others",
                cls="btn btn-error btn-outline",
                hx_post="/settings/sessions/revoke-all",
                hx_confirm="Revoke all other sessions?",
            ),
            cls="flex justify-between items-center mb-6",
        ),
        Table(
            Thead(
                Tr(
                    Th("Device"),
                    Th("Client"),
                    Th("IP Address"),
                    Th("Last Active"),
                    Th("Actions"),
                )
            ),
            Tbody(*session_rows),
            cls="table w-full",
        ),
    )

    return page_layout(content, title="Sessions - LinkJot", user=user)


def settings_session_revoke(request, db, session_id: str):
    """Revoke a specific session.

    POST /settings/sessions/{id}/revoke
    """
    result = require_auth(request, db)
    if isinstance(result, Response):
        return result
    user, current_token = result

    # Don't allow revoking current session
    if session_id == current_token:
        return Response("Cannot revoke current session", status_code=400)

    session = database.get_session(db, session_id)
    if not session or session.user_id != user.id:
        return Response("Not found", status_code=404)

    database.delete_session(db, session_id)

    return Response("")


def settings_sessions_revoke_all(request, db):
    """Revoke all other sessions.

    POST /settings/sessions/revoke-all
    """
    result = require_auth(request, db)
    if isinstance(result, Response):
        return result
    user, current_token = result

    database.delete_user_sessions(db, user.id, except_session=current_token)

    response = Response(status_code=200)
    response.headers["HX-Redirect"] = "/settings/sessions"
    return response


def export_page(request, db):
    """Export bookmarks as JSON download.

    GET /export
    """
    result = require_auth(request, db)
    if isinstance(result, Response):
        return result
    user, _ = result

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
                "created_at": b.created_at,
            })
        offset += 500
        if len(batch) < 500:
            break

    export_data = {
        "bookmarks": bookmarks,
        "exported_at": now_iso(),
        "count": len(bookmarks),
    }

    return Response(
        json.dumps(export_data, indent=2),
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename=linkjot-export-{now_iso()[:10]}.json"
        }
    )
