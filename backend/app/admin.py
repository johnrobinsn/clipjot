"""Admin UI views for ClipJot.

Admin-only routes for user management and system statistics.
Privacy constraint: Admins can see counts but NOT user content.
"""

import os
from typing import Optional
from fasthtml.common import *

from . import config
from . import db as database
from .models import User
from .components import page_layout, pagination
from .views import get_current_user


# =============================================================================
# Admin Helpers
# =============================================================================

def require_admin(request, db):
    """Require admin authentication.

    Returns (user, session_token) or raises RedirectResponse/Response.
    """
    result = get_current_user(request, db)
    if not result:
        return RedirectResponse("/login", status_code=303)

    user, session_token = result
    if not user.is_admin:
        return Response("Admin access required", status_code=403)

    return user, session_token


# =============================================================================
# Admin Dashboard
# =============================================================================

def admin_dashboard(request, db):
    """Admin dashboard with system statistics.

    GET /admin
    """
    result = require_admin(request, db)
    if isinstance(result, Response):
        return result
    user, _ = result

    # Gather stats
    total_users = database.count_all_users(db)
    total_bookmarks = database.count_all_bookmarks(db)
    active_sessions = database.count_active_sessions(db)

    # Database size
    try:
        db_size = os.path.getsize(config.DATABASE_PATH)
        db_size_str = f"{db_size / 1024 / 1024:.2f} MB"
    except Exception:
        db_size_str = "Unknown"

    # Recent user counts
    from datetime import datetime, timedelta
    now = datetime.utcnow()
    week_ago = (now - timedelta(days=7)).isoformat()
    month_ago = (now - timedelta(days=30)).isoformat()

    users_last_week = db.execute(
        f"SELECT COUNT(*) FROM user WHERE created_at >= '{week_ago}'"
    ).fetchone()[0]
    users_last_month = db.execute(
        f"SELECT COUNT(*) FROM user WHERE created_at >= '{month_ago}'"
    ).fetchone()[0]

    # Premium and admin counts
    premium_users = db.execute("SELECT COUNT(*) FROM user WHERE is_premium = 1").fetchone()[0]
    admin_users = db.execute("SELECT COUNT(*) FROM user WHERE is_admin = 1").fetchone()[0]
    suspended_users = db.execute("SELECT COUNT(*) FROM user WHERE is_suspended = 1").fetchone()[0]

    content = Div(
        children=[
            H1("Admin Dashboard", cls="text-2xl font-bold mb-6"),

            # Stats grid
            Div(
                cls="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8",
                children=[
                    # Users stat
                    Div(
                        cls="stat bg-base-100 rounded-lg shadow",
                        children=[
                            Div("Total Users", cls="stat-title"),
                            Div(str(total_users), cls="stat-value"),
                            Div(f"+{users_last_week} this week", cls="stat-desc"),
                        ]
                    ),
                    # Bookmarks stat
                    Div(
                        cls="stat bg-base-100 rounded-lg shadow",
                        children=[
                            Div("Total Bookmarks", cls="stat-title"),
                            Div(str(total_bookmarks), cls="stat-value"),
                            Div("across all users", cls="stat-desc"),
                        ]
                    ),
                    # Sessions stat
                    Div(
                        cls="stat bg-base-100 rounded-lg shadow",
                        children=[
                            Div("Active Sessions", cls="stat-title"),
                            Div(str(active_sessions), cls="stat-value"),
                        ]
                    ),
                    # Database stat
                    Div(
                        cls="stat bg-base-100 rounded-lg shadow",
                        children=[
                            Div("Database Size", cls="stat-title"),
                            Div(db_size_str, cls="stat-value"),
                        ]
                    ),
                ]
            ),

            # User breakdown
            Div(
                cls="card bg-base-100 shadow-xl mb-6",
                children=[
                    Div(
                        cls="card-body",
                        children=[
                            H2("User Breakdown", cls="card-title"),
                            Div(
                                cls="overflow-x-auto",
                                children=[
                                    Table(
                                        cls="table",
                                        children=[
                                            Tbody(
                                                Tr(Td("Total Users"), Td(str(total_users))),
                                                Tr(Td("New (last 7 days)"), Td(str(users_last_week))),
                                                Tr(Td("New (last 30 days)"), Td(str(users_last_month))),
                                                Tr(Td("Premium Users"), Td(str(premium_users))),
                                                Tr(Td("Admin Users"), Td(str(admin_users))),
                                                Tr(Td("Suspended Users"), Td(str(suspended_users))),
                                            ),
                                        ]
                                    ),
                                ]
                            ),
                        ]
                    ),
                ]
            ),

            # Quick links
            Div(
                cls="flex gap-4",
                children=[
                    A("Manage Users", href="/admin/users", cls="btn btn-primary"),
                ]
            ),
        ]
    )

    return page_layout(content, title="Admin Dashboard - ClipJot", user=user)


# =============================================================================
# User Management
# =============================================================================

def admin_users(request, db):
    """User management list.

    GET /admin/users
    """
    result = require_admin(request, db)
    if isinstance(result, Response):
        return result
    user, _ = result

    # Get query params
    search = request.query_params.get("q", "").strip()
    status_filter = request.query_params.get("status", "all")
    page = int(request.query_params.get("page", 1))
    per_page = 50

    # Build query
    where_clauses = []
    if search:
        safe_search = search.replace("'", "''")
        where_clauses.append(f"email LIKE '%{safe_search}%'")
    if status_filter == "active":
        where_clauses.append("is_suspended = 0")
    elif status_filter == "suspended":
        where_clauses.append("is_suspended = 1")
    elif status_filter == "premium":
        where_clauses.append("is_premium = 1")

    where = " AND ".join(where_clauses) if where_clauses else None

    # Get users
    users = list(db.t.user(
        where=where,
        order_by="created_at DESC",
        limit=per_page,
        offset=(page - 1) * per_page,
    ))

    # Count total
    count_query = "SELECT COUNT(*) FROM user"
    if where:
        count_query += f" WHERE {where}"
    total = db.execute(count_query).fetchone()[0]

    # Get stats for each user (counts only, not content)
    user_rows = []
    for u in users:
        stats = database.get_user_stats(db, u.id)
        user_rows.append((u, stats))

    content = Div(
        children=[
            H1("User Management", cls="text-2xl font-bold mb-6"),

            # Search and filters
            Form(
                cls="flex gap-4 mb-6",
                action="/admin/users",
                method="get",
                children=[
                    Input(
                        type="search",
                        name="q",
                        value=search,
                        placeholder="Search by email...",
                        cls="input input-bordered flex-1",
                    ),
                    Select(
                        name="status",
                        cls="select select-bordered",
                        children=[
                            Option("All Users", value="all", selected=status_filter == "all"),
                            Option("Active", value="active", selected=status_filter == "active"),
                            Option("Suspended", value="suspended", selected=status_filter == "suspended"),
                            Option("Premium", value="premium", selected=status_filter == "premium"),
                        ]
                    ),
                    Button("Search", type="submit", cls="btn btn-primary"),
                ]
            ),

            # Results info
            P(f"Showing {len(users)} of {total} users", cls="text-sm text-base-content/70 mb-4"),

            # User table
            Table(
                cls="table w-full",
                children=[
                    Thead(
                        Tr(
                            Th("Email"),
                            Th("Created"),
                            Th("Bookmarks"),
                            Th("Tags"),
                            Th("Status"),
                            Th("Actions"),
                        )
                    ),
                    Tbody(
                        children=[
                            Tr(
                                children=[
                                    Td(
                                        A(u.email, href=f"/admin/users/{u.id}", cls="link link-primary"),
                                    ),
                                    Td(u.created_at[:10] if u.created_at else ""),
                                    Td(str(stats["bookmark_count"])),
                                    Td(str(stats["tag_count"])),
                                    Td(
                                        Div(
                                            cls="flex gap-1",
                                            children=[
                                                Span("Suspended", cls="badge badge-error") if u.is_suspended else None,
                                                Span("Premium", cls="badge badge-success") if u.is_premium else None,
                                                Span("Admin", cls="badge badge-warning") if u.is_admin else None,
                                                Span("Active", cls="badge") if not u.is_suspended and not u.is_premium and not u.is_admin else None,
                                            ]
                                        )
                                    ),
                                    Td(
                                        A("View", href=f"/admin/users/{u.id}", cls="btn btn-xs btn-ghost"),
                                    ),
                                ]
                            )
                            for u, stats in user_rows
                        ],
                    ),
                ]
            ),

            # Pagination
            pagination(
                page, total, per_page,
                f"/admin/users?q={search}&status={status_filter}"
            ),
        ]
    )

    return page_layout(content, title="User Management - ClipJot", user=user)


def admin_user_detail(request, db, user_id: int):
    """User detail page (counts only, no content).

    GET /admin/users/{id}
    """
    result = require_admin(request, db)
    if isinstance(result, Response):
        return result
    admin_user, _ = result

    target_user = database.get_user_by_id(db, user_id)
    if not target_user:
        return Response("User not found", status_code=404)

    stats = database.get_user_stats(db, user_id)

    # Get last login (most recent session)
    sessions = database.get_user_sessions(db, user_id)
    last_login = max((s.created_at for s in sessions), default=None) if sessions else None

    content = Div(
        children=[
            # Header with back link
            Div(
                cls="flex items-center gap-4 mb-6",
                children=[
                    A("Back to Users", href="/admin/users", cls="btn btn-ghost btn-sm"),
                    H1(f"User: {target_user.email}", cls="text-2xl font-bold"),
                ]
            ),

            # User info card
            Div(
                cls="card bg-base-100 shadow-xl mb-6",
                children=[
                    Div(
                        cls="card-body",
                        children=[
                            H2("Account Information", cls="card-title"),
                            Table(
                                cls="table",
                                children=[
                                    Tbody(
                                        Tr(Th("Email"), Td(target_user.email)),
                                        Tr(Th("Created"), Td(target_user.created_at[:16] if target_user.created_at else "Unknown")),
                                        Tr(Th("Last Login"), Td(last_login[:16] if last_login else "Never")),
                                        Tr(Th("Premium"), Td("Yes" if target_user.is_premium else "No")),
                                        Tr(Th("Admin"), Td("Yes" if target_user.is_admin else "No")),
                                        Tr(
                                            Th("Status"),
                                            Td(
                                                Div(
                                                    Span("Suspended", cls="badge badge-error"),
                                                    Span(f" - {target_user.suspended_reason}", cls="text-sm")
                                                    if target_user.suspended_reason else None,
                                                ) if target_user.is_suspended else
                                                Span("Active", cls="badge badge-success")
                                            )
                                        ),
                                    ),
                                ]
                            ),
                        ]
                    ),
                ]
            ),

            # Stats card (counts only, not content)
            Div(
                cls="card bg-base-100 shadow-xl mb-6",
                children=[
                    Div(
                        cls="card-body",
                        children=[
                            H2("Usage Statistics", cls="card-title"),
                            P("Aggregate counts only - bookmark content is private", cls="text-sm text-base-content/70 mb-4"),
                            Div(
                                cls="stats stats-vertical lg:stats-horizontal shadow",
                                children=[
                                    Div(
                                        cls="stat",
                                        children=[
                                            Div("Bookmarks", cls="stat-title"),
                                            Div(str(stats["bookmark_count"]), cls="stat-value"),
                                        ]
                                    ),
                                    Div(
                                        cls="stat",
                                        children=[
                                            Div("Tags", cls="stat-title"),
                                            Div(str(stats["tag_count"]), cls="stat-value"),
                                        ]
                                    ),
                                    Div(
                                        cls="stat",
                                        children=[
                                            Div("Sessions", cls="stat-title"),
                                            Div(str(stats["session_count"]), cls="stat-value"),
                                        ]
                                    ),
                                    Div(
                                        cls="stat",
                                        children=[
                                            Div("API Tokens", cls="stat-title"),
                                            Div(str(stats["token_count"]), cls="stat-value"),
                                        ]
                                    ),
                                ]
                            ),
                        ]
                    ),
                ]
            ),

            # Admin actions
            Div(
                cls="card bg-base-100 shadow-xl",
                children=[
                    Div(
                        cls="card-body",
                        children=[
                            H2("Admin Actions", cls="card-title"),

                            Div(
                                cls="flex flex-wrap gap-4",
                                children=[
                                    # Premium toggle
                                    Form(
                                        action=f"/admin/users/{user_id}/premium",
                                        method="post",
                                        children=[
                                            Button(
                                                "Remove Premium" if target_user.is_premium else "Grant Premium",
                                                type="submit",
                                                cls=f"btn {'btn-warning' if target_user.is_premium else 'btn-success'}",
                                            ),
                                        ]
                                    ),

                                    # Suspend/unsuspend
                                    Form(
                                        action=f"/admin/users/{user_id}/{'unsuspend' if target_user.is_suspended else 'suspend'}",
                                        method="post",
                                        cls="flex gap-2",
                                        children=[
                                            Input(
                                                type="text",
                                                name="reason",
                                                placeholder="Suspension reason...",
                                                cls="input input-bordered",
                                            ) if not target_user.is_suspended else None,
                                            Button(
                                                "Unsuspend" if target_user.is_suspended else "Suspend",
                                                type="submit",
                                                cls=f"btn {'btn-success' if target_user.is_suspended else 'btn-error'}",
                                            ),
                                        ]
                                    ),

                                    # Terminate sessions
                                    Form(
                                        action=f"/admin/users/{user_id}/terminate-sessions",
                                        method="post",
                                        children=[
                                            Button(
                                                "Terminate All Sessions",
                                                type="submit",
                                                cls="btn btn-warning",
                                                onclick="return confirm('Terminate all sessions for this user?')",
                                            ),
                                        ]
                                    ),

                                    # Delete user
                                    Form(
                                        action=f"/admin/users/{user_id}/delete",
                                        method="post",
                                        children=[
                                            Button(
                                                "Delete User",
                                                type="submit",
                                                cls="btn btn-error",
                                                onclick="return confirm('DELETE THIS USER AND ALL THEIR DATA? This cannot be undone!')",
                                            ),
                                        ]
                                    ),
                                ]
                            ),
                        ]
                    ),
                ]
            ),
        ]
    )

    return page_layout(content, title=f"User: {target_user.email} - ClipJot", user=admin_user)


# =============================================================================
# Admin Actions
# =============================================================================

def admin_user_premium(request, db, user_id: int):
    """Toggle premium status.

    POST /admin/users/{id}/premium
    """
    result = require_admin(request, db)
    if isinstance(result, Response):
        return result

    target_user = database.get_user_by_id(db, user_id)
    if not target_user:
        return Response("User not found", status_code=404)

    target_user.is_premium = not target_user.is_premium
    database.update_user(db, target_user)

    return RedirectResponse(f"/admin/users/{user_id}", status_code=303)


def admin_user_suspend(request, db, user_id: int):
    """Suspend a user.

    POST /admin/users/{id}/suspend
    """
    result = require_admin(request, db)
    if isinstance(result, Response):
        return result

    target_user = database.get_user_by_id(db, user_id)
    if not target_user:
        return Response("User not found", status_code=404)

    form = request.form()
    reason = form.get("reason", "").strip()

    target_user.is_suspended = True
    target_user.suspended_at = database.now_iso()
    target_user.suspended_reason = reason or "No reason provided"
    database.update_user(db, target_user)

    # Terminate all sessions
    database.delete_user_sessions(db, user_id)

    return RedirectResponse(f"/admin/users/{user_id}", status_code=303)


def admin_user_unsuspend(request, db, user_id: int):
    """Unsuspend a user.

    POST /admin/users/{id}/unsuspend
    """
    result = require_admin(request, db)
    if isinstance(result, Response):
        return result

    target_user = database.get_user_by_id(db, user_id)
    if not target_user:
        return Response("User not found", status_code=404)

    target_user.is_suspended = False
    target_user.suspended_at = None
    target_user.suspended_reason = None
    database.update_user(db, target_user)

    return RedirectResponse(f"/admin/users/{user_id}", status_code=303)


def admin_user_terminate_sessions(request, db, user_id: int):
    """Terminate all sessions for a user.

    POST /admin/users/{id}/terminate-sessions
    """
    result = require_admin(request, db)
    if isinstance(result, Response):
        return result

    target_user = database.get_user_by_id(db, user_id)
    if not target_user:
        return Response("User not found", status_code=404)

    database.delete_user_sessions(db, user_id)

    return RedirectResponse(f"/admin/users/{user_id}", status_code=303)


def admin_user_delete(request, db, user_id: int):
    """Delete a user and all their data.

    POST /admin/users/{id}/delete
    """
    result = require_admin(request, db)
    if isinstance(result, Response):
        return result

    target_user = database.get_user_by_id(db, user_id)
    if not target_user:
        return Response("User not found", status_code=404)

    # Don't allow deleting yourself
    admin_user, _ = result
    if target_user.id == admin_user.id:
        return Response("Cannot delete yourself", status_code=400)

    database.delete_user(db, user_id)

    return RedirectResponse("/admin/users", status_code=303)
