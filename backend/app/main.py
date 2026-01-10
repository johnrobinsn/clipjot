"""ClipJot FastHTML Application Entry Point.

This module creates and configures the FastHTML application,
registers all routes, and sets up OAuth authentication.
"""

import json
from pathlib import Path
from fasthtml.common import *
from starlette.responses import FileResponse

from . import config

# Static files directory
_static_dir = Path(__file__).parent.parent / "static"
from . import db as database
from . import views
from . import admin
from . import api


# =============================================================================
# Application Setup
# =============================================================================

# Create FastHTML app
app = FastHTML(
    secret_key=config.SECRET_KEY,
    hdrs=[
        # Favicon
        Link(rel="icon", type="image/png", href="/static/favicon.png"),
        # DaisyUI + Tailwind CSS
        Link(rel="stylesheet", href="https://cdn.jsdelivr.net/npm/daisyui@4/dist/full.min.css"),
        Script(src="https://cdn.tailwindcss.com"),
        # HTMX
        Script(src="https://unpkg.com/htmx.org@1.9.10"),
    ],
)

# Get route decorator
rt = app.route


# Database getter for dependency injection
def get_db():
    return database.get_db()


# Static file serving
@rt("/static/{filename:path}")
async def static_file(filename: str):
    """Serve static files."""
    file_path = _static_dir / filename
    if file_path.exists() and file_path.is_file():
        return FileResponse(file_path)
    return Response("Not found", status_code=404)


# =============================================================================
# OAuth Setup
# =============================================================================

# Note: OAuth clients need to be configured with actual credentials
# These are placeholder implementations that will be connected to FastHTML's OAuth

if config.has_google_oauth():
    try:
        from fasthtml.oauth import GoogleAppClient
        google_client = GoogleAppClient(
            config.GOOGLE_CLIENT_ID,
            config.GOOGLE_CLIENT_SECRET,
        )
    except ImportError:
        google_client = None
else:
    google_client = None

if config.has_github_oauth():
    try:
        from fasthtml.oauth import GitHubAppClient
        github_client = GitHubAppClient(
            config.GITHUB_CLIENT_ID,
            config.GITHUB_CLIENT_SECRET,
        )
    except ImportError:
        github_client = None
else:
    github_client = None


# =============================================================================
# Public Routes
# =============================================================================

@rt("/login")
def login_page(request):
    return views.login_page(request, get_db())


@rt("/health")
def health_check(request):
    return views.health_check(request, get_db())


@rt("/debug/session")
def debug_session(request):
    """Debug endpoint to check session cookie status."""
    from starlette.responses import JSONResponse
    session_cookie = request.cookies.get("session")

    if not session_cookie:
        return JSONResponse({
            "status": "no_cookie",
            "message": "No session cookie found in request",
            "all_cookies": dict(request.cookies),
        })

    db = get_db()
    from app import db as database
    session = database.get_session(db, session_cookie)

    if not session:
        return JSONResponse({
            "status": "invalid_session",
            "message": "Session cookie found but session not in database or expired",
            "cookie_prefix": session_cookie[:20] + "...",
        })

    return JSONResponse({
        "status": "valid",
        "message": "Session is valid",
        "session_id_prefix": session.id[:20] + "...",
        "user_id": session.user_id,
        "expires_at": session.expires_at,
        "created_at": session.created_at,
    })


@rt("/logout", methods=["POST"])
def logout(request):
    return views.logout(request, get_db())


# =============================================================================
# OAuth Routes
# =============================================================================

@rt("/auth/google")
def auth_google(request, redirect_uri: str = None):
    """Start Google OAuth. If redirect_uri is provided (extension flow), encode it in state."""
    if not google_client:
        return Response("Google OAuth not configured", status_code=503)
    oauth_redirect = f"{config.BASE_URL}/auth_redirect/google"
    # If redirect_uri provided, this is extension flow - encode in state
    state = None
    if redirect_uri:
        import base64
        state = base64.urlsafe_b64encode(f"ext:{redirect_uri}".encode()).decode()
    login_url = google_client.login_link(oauth_redirect, state=state)
    return RedirectResponse(login_url, status_code=303)


@rt("/auth_redirect/google")
def auth_redirect_google(request, code: str = None, state: str = None):
    if not google_client:
        return Response("Google OAuth not configured", status_code=503)
    if not code:
        return RedirectResponse("/login", status_code=303)

    try:
        oauth_redirect = f"{config.BASE_URL}/auth_redirect/google"
        user_info = google_client.retr_info(code, oauth_redirect)

        # Check if this is extension flow (state starts with "ext:")
        if state:
            import base64
            try:
                decoded = base64.urlsafe_b64decode(state.encode()).decode()
                if decoded.startswith("ext:"):
                    extension_redirect = decoded[4:]  # Remove "ext:" prefix
                    return views.oauth_extension_callback(request, get_db(), "google", user_info, extension_redirect)
            except Exception:
                pass  # Invalid state, fall through to web flow

        return views.oauth_callback_handler(request, get_db(), "google", user_info)
    except Exception as e:
        return Response(f"OAuth error: {e}", status_code=400)


@rt("/auth/github")
def auth_github(request, redirect_uri: str = None):
    """Start GitHub OAuth. If redirect_uri is provided (extension flow), encode it in state."""
    if not github_client:
        return Response("GitHub OAuth not configured", status_code=503)
    oauth_redirect = f"{config.BASE_URL}/auth_redirect/github"
    # If redirect_uri provided, this is extension flow - encode in state
    state = None
    if redirect_uri:
        import base64
        state = base64.urlsafe_b64encode(f"ext:{redirect_uri}".encode()).decode()
    login_url = github_client.login_link(oauth_redirect, state=state)
    return RedirectResponse(login_url, status_code=303)


@rt("/auth_redirect/github")
def auth_redirect_github(request, code: str = None, state: str = None):
    if not github_client:
        return Response("GitHub OAuth not configured", status_code=503)
    if not code:
        return RedirectResponse("/login", status_code=303)

    try:
        oauth_redirect = f"{config.BASE_URL}/auth_redirect/github"
        user_info = github_client.retr_info(code, oauth_redirect)

        # Check if this is extension flow (state starts with "ext:")
        if state:
            import base64
            try:
                decoded = base64.urlsafe_b64decode(state.encode()).decode()
                if decoded.startswith("ext:"):
                    extension_redirect = decoded[4:]  # Remove "ext:" prefix
                    return views.oauth_extension_callback(request, get_db(), "github", user_info, extension_redirect)
            except Exception:
                pass  # Invalid state, fall through to web flow

        return views.oauth_callback_handler(request, get_db(), "github", user_info)
    except Exception as e:
        return Response(f"OAuth error: {e}", status_code=400)


# =============================================================================
# Bookmark Routes
# =============================================================================

@rt("/")
def index(request):
    return views.bookmark_index(request, get_db())


@rt("/bookmarks/add", methods=["GET"])
def bookmark_add_form(request):
    return views.bookmark_add_form(request, get_db())


@rt("/bookmarks/add", methods=["POST"])
async def bookmark_add(request):
    return await views.bookmark_add(request, get_db())


@rt("/bookmarks/{bookmark_id}/edit")
def bookmark_edit_form(request, bookmark_id: int):
    return views.bookmark_edit_form(request, get_db(), bookmark_id)


@rt("/bookmarks/{bookmark_id}", methods=["POST"])
async def bookmark_edit(request, bookmark_id: int):
    return await views.bookmark_edit(request, get_db(), bookmark_id)


@rt("/bookmarks/bulk", methods=["DELETE"])
async def bookmark_bulk_delete(request):
    return await views.bookmark_bulk_delete(request, get_db())


@rt("/bookmarks/bulk/add-tag", methods=["POST"])
async def bookmark_bulk_add_tag_form(request):
    return await views.bookmark_bulk_add_tag_form(request, get_db())


@rt("/bookmarks/bulk/add-tag/apply", methods=["POST"])
async def bookmark_bulk_add_tag(request):
    return await views.bookmark_bulk_add_tag(request, get_db())


@rt("/bookmarks/bulk/remove-tag", methods=["POST"])
async def bookmark_bulk_remove_tag_form(request):
    return await views.bookmark_bulk_remove_tag_form(request, get_db())


@rt("/bookmarks/bulk/remove-tag/apply", methods=["POST"])
async def bookmark_bulk_remove_tag(request):
    return await views.bookmark_bulk_remove_tag(request, get_db())


@rt("/bookmarks/{bookmark_id}", methods=["DELETE"])
def bookmark_delete(request, bookmark_id: int):
    return views.bookmark_delete(request, get_db(), bookmark_id)


# =============================================================================
# Settings Routes
# =============================================================================

@rt("/settings")
def settings_page(request):
    return views.settings_page(request, get_db())


@rt("/settings/tags")
def settings_tags(request):
    return views.settings_tags(request, get_db())


@rt("/settings/tags/add", methods=["GET"])
def settings_tag_add_form(request):
    return views.settings_tag_add_form(request, get_db())


@rt("/settings/tags/add", methods=["POST"])
async def settings_tag_add(request):
    return await views.settings_tag_add(request, get_db())


@rt("/settings/tags/{tag_id}", methods=["DELETE"])
def settings_tag_delete(request, tag_id: int):
    return views.settings_tag_delete(request, get_db(), tag_id)


@rt("/settings/tokens")
def settings_tokens(request):
    return views.settings_tokens(request, get_db())


@rt("/settings/tokens/create", methods=["GET"])
def settings_token_create_form(request):
    return views.settings_token_create_form(request, get_db())


@rt("/settings/tokens/create", methods=["POST"])
async def settings_token_create(request):
    return await views.settings_token_create(request, get_db())


@rt("/settings/tokens/{token_id}", methods=["DELETE"])
def settings_token_delete(request, token_id: int):
    return views.settings_token_delete(request, get_db(), token_id)


@rt("/settings/sessions")
def settings_sessions(request):
    return views.settings_sessions(request, get_db())


@rt("/settings/sessions/{session_id}/revoke", methods=["POST"])
async def settings_session_revoke(request, session_id: str):
    return views.settings_session_revoke(request, get_db(), session_id)


@rt("/settings/sessions/revoke-all", methods=["POST"])
async def settings_sessions_revoke_all(request):
    return views.settings_sessions_revoke_all(request, get_db())


@rt("/export")
def export_page(request):
    return views.export_page(request, get_db())


@rt("/export/download")
def export_download(request):
    return views.export_download(request, get_db())


# =============================================================================
# Admin Routes
# =============================================================================

@rt("/admin")
def admin_dashboard(request):
    return admin.admin_dashboard(request, get_db())


@rt("/admin/users")
def admin_users(request):
    return admin.admin_users(request, get_db())


@rt("/admin/users/{user_id}")
def admin_user_detail(request, user_id: int):
    return admin.admin_user_detail(request, get_db(), user_id)


@rt("/admin/users/{user_id}/premium", methods=["POST"])
async def admin_user_premium(request, user_id: int):
    return admin.admin_user_premium(request, get_db(), user_id)


@rt("/admin/users/{user_id}/suspend", methods=["POST"])
async def admin_user_suspend(request, user_id: int):
    return admin.admin_user_suspend(request, get_db(), user_id)


@rt("/admin/users/{user_id}/unsuspend", methods=["POST"])
async def admin_user_unsuspend(request, user_id: int):
    return admin.admin_user_unsuspend(request, get_db(), user_id)


@rt("/admin/users/{user_id}/terminate-sessions", methods=["POST"])
async def admin_user_terminate_sessions(request, user_id: int):
    return admin.admin_user_terminate_sessions(request, get_db(), user_id)


@rt("/admin/users/{user_id}/delete", methods=["POST"])
async def admin_user_delete(request, user_id: int):
    return admin.admin_user_delete(request, get_db(), user_id)


# =============================================================================
# API Routes
# =============================================================================

async def parse_json_body(request):
    """Parse JSON body from request."""
    try:
        body = await request.body()
        return json.loads(body) if body else {}
    except json.JSONDecodeError:
        return {}


@rt("/api/v1/logout", methods=["POST"])
async def api_logout(request):
    data = await parse_json_body(request)
    return api.api_logout(request, get_db(), data)


@rt("/api/v1/bookmarks/add", methods=["POST"])
async def api_bookmarks_add(request):
    data = await parse_json_body(request)
    return api.api_bookmarks_add(request, get_db(), data)


@rt("/api/v1/bookmarks/edit", methods=["POST"])
async def api_bookmarks_edit(request):
    data = await parse_json_body(request)
    return api.api_bookmarks_edit(request, get_db(), data)


@rt("/api/v1/bookmarks/delete", methods=["POST"])
async def api_bookmarks_delete(request):
    data = await parse_json_body(request)
    return api.api_bookmarks_delete(request, get_db(), data)


@rt("/api/v1/bookmarks/search", methods=["POST"])
async def api_bookmarks_search(request):
    data = await parse_json_body(request)
    return api.api_bookmarks_search(request, get_db(), data)


@rt("/api/v1/bookmarks/list", methods=["POST"])
async def api_bookmarks_list(request):
    data = await parse_json_body(request)
    return api.api_bookmarks_list(request, get_db(), data)


@rt("/api/v1/tags/list", methods=["POST"])
async def api_tags_list(request):
    data = await parse_json_body(request)
    return api.api_tags_list(request, get_db(), data)


@rt("/api/v1/tags/create", methods=["POST"])
async def api_tags_create(request):
    data = await parse_json_body(request)
    return api.api_tags_create(request, get_db(), data)


@rt("/api/v1/tags/update", methods=["POST"])
async def api_tags_update(request):
    data = await parse_json_body(request)
    return api.api_tags_update(request, get_db(), data)


@rt("/api/v1/tags/delete", methods=["POST"])
async def api_tags_delete(request):
    data = await parse_json_body(request)
    return api.api_tags_delete(request, get_db(), data)


@rt("/api/v1/export", methods=["POST"])
async def api_export(request):
    data = await parse_json_body(request)
    return api.api_export(request, get_db(), data)


@rt("/api/v1/import", methods=["POST"])
async def api_import(request):
    data = await parse_json_body(request)
    return api.api_import(request, get_db(), data)


# =============================================================================
# Run Server
# =============================================================================

# Simple ASGI app that redirects HTTP to HTTPS
async def https_redirect_app(scope, receive, send):
    """Redirect all HTTP requests to HTTPS."""
    if scope["type"] == "http":
        host = None
        for header_name, header_value in scope.get("headers", []):
            if header_name == b"host":
                host = header_value.decode("utf-8").split(":")[0]  # Remove port if present
                break

        path = scope.get("path", "/")
        query_string = scope.get("query_string", b"")

        # Build HTTPS URL using configured port
        redirect_url = f"https://{host}:{config.PORT}{path}"
        if query_string:
            redirect_url += f"?{query_string.decode('utf-8')}"

        await send({
            "type": "http.response.start",
            "status": 301,
            "headers": [
                [b"location", redirect_url.encode("utf-8")],
                [b"content-type", b"text/html"],
            ],
        })
        await send({
            "type": "http.response.body",
            "body": f'<html><body>Redirecting to <a href="{redirect_url}">{redirect_url}</a></body></html>'.encode("utf-8"),
        })


def main():
    """Run the development server."""
    import uvicorn
    import threading

    main_port = config.PORT

    uvicorn_kwargs = {
        "host": "0.0.0.0",
        "port": main_port,
        "reload": True,
    }

    # Add SSL configuration if certificates are specified
    if config.has_ssl_config():
        uvicorn_kwargs["ssl_certfile"] = config.SSL_CERT_FILE
        uvicorn_kwargs["ssl_keyfile"] = config.SSL_KEY_FILE

        # Start HTTP redirect server in a separate thread
        http_port = config.SSL_REDIRECT_PORT

        def run_redirect_server():
            uvicorn.run(
                "app.main:https_redirect_app",
                host="0.0.0.0",
                port=http_port,
                log_level="info",
            )

        redirect_thread = threading.Thread(target=run_redirect_server, daemon=True)
        redirect_thread.start()
        print(f"HTTP redirect server running on port {http_port} -> HTTPS port {main_port}")

    uvicorn.run("app.main:app", **uvicorn_kwargs)


if __name__ == "__main__":
    main()
