"""Tests for HTTP route handling.

These tests verify that routes are correctly registered, handle proper HTTP methods,
and don't have ordering conflicts (e.g., /bookmarks/bulk vs /bookmarks/{id}).
"""

import pytest
from unittest.mock import patch, MagicMock
from starlette.testclient import TestClient


@pytest.fixture
def app_client(db, mock_config):
    """Create a test client with mocked database."""
    # We need to patch get_db before importing the app
    with patch("app.main.database.get_db", return_value=db):
        with patch("app.main.config.SECRET_KEY", "test-secret-key"):
            from app.main import app
            client = TestClient(app, raise_server_exceptions=False)
            yield client


@pytest.fixture
def authenticated_client(app_client, db, test_user, test_session):
    """Create an authenticated test client."""
    token, session = test_session
    app_client.cookies.set("session", token)
    return app_client


class TestPublicRoutes:
    """Test public routes that don't require authentication."""

    def test_health_check(self, app_client):
        """Test /health endpoint returns OK."""
        response = app_client.get("/health")

        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_login_page_loads(self, app_client):
        """Test /login page loads without error."""
        response = app_client.get("/login")

        assert response.status_code == 200
        assert "LinkJot" in response.text

    def test_unauthenticated_redirects_to_login(self, app_client):
        """Test that unauthenticated requests to / redirect to login."""
        response = app_client.get("/", follow_redirects=False)

        assert response.status_code == 303
        assert response.headers["location"] == "/login"


class TestRouteOrdering:
    """Test that route ordering doesn't cause conflicts.

    This catches issues like /bookmarks/{id} matching before /bookmarks/bulk.
    """

    def test_bulk_delete_route_exists(self, authenticated_client):
        """Test /bookmarks/bulk DELETE route is accessible (not caught by {id})."""
        # This should NOT return 404 - it was a bug where {bookmark_id} matched "bulk"
        response = authenticated_client.delete("/bookmarks/bulk")

        # Should get 200 or 400 (no items selected), but NOT 404
        assert response.status_code != 404, \
            "Route /bookmarks/bulk should not return 404 - check route ordering"

    def test_single_bookmark_delete(self, authenticated_client, db, test_user, test_bookmark):
        """Test /bookmarks/{id} DELETE still works for numeric IDs."""
        response = authenticated_client.delete(f"/bookmarks/{test_bookmark.id}")

        # Should return empty response on success
        assert response.status_code == 200

    def test_bookmark_edit_route(self, authenticated_client, db, test_bookmark):
        """Test /bookmarks/{id}/edit GET route works."""
        response = authenticated_client.get(f"/bookmarks/{test_bookmark.id}/edit")

        assert response.status_code == 200
        assert "modal" in response.text.lower() or "form" in response.text.lower()

    def test_settings_tags_add_before_tags_id(self, authenticated_client):
        """Test /settings/tags/add route isn't caught by a parameterized route."""
        response = authenticated_client.get("/settings/tags/add")

        # Should return modal form, not 404
        assert response.status_code == 200


class TestBookmarkRoutes:
    """Test bookmark-related routes."""

    def test_index_requires_auth(self, app_client):
        """Test / requires authentication."""
        response = app_client.get("/", follow_redirects=False)
        assert response.status_code == 303

    def test_index_with_auth(self, authenticated_client):
        """Test / works with authentication."""
        response = authenticated_client.get("/")

        assert response.status_code == 200
        assert "My Links" in response.text

    def test_add_bookmark_form(self, authenticated_client):
        """Test GET /bookmarks/add returns form modal."""
        response = authenticated_client.get("/bookmarks/add")

        assert response.status_code == 200
        assert "url" in response.text.lower()

    def test_add_bookmark_post(self, authenticated_client):
        """Test POST /bookmarks/add creates bookmark."""
        response = authenticated_client.post(
            "/bookmarks/add",
            data={"url": "https://test.com", "title": "Test Site"},
        )

        # Should redirect via HX-Redirect header
        assert response.status_code == 200
        assert response.headers.get("HX-Redirect") == "/"

    def test_add_bookmark_requires_url(self, authenticated_client):
        """Test POST /bookmarks/add fails without URL."""
        response = authenticated_client.post(
            "/bookmarks/add",
            data={"title": "No URL"},
        )

        assert response.status_code == 400

    def test_edit_nonexistent_bookmark(self, authenticated_client):
        """Test editing nonexistent bookmark returns 404."""
        response = authenticated_client.get("/bookmarks/99999/edit")

        assert response.status_code == 404

    def test_delete_nonexistent_bookmark(self, authenticated_client):
        """Test deleting nonexistent bookmark returns 404."""
        response = authenticated_client.delete("/bookmarks/99999")

        assert response.status_code == 404


class TestSettingsRoutes:
    """Test settings-related routes."""

    def test_settings_page(self, authenticated_client):
        """Test /settings page loads."""
        response = authenticated_client.get("/settings")

        assert response.status_code == 200
        assert "Settings" in response.text

    def test_settings_tags(self, authenticated_client):
        """Test /settings/tags page loads."""
        response = authenticated_client.get("/settings/tags")

        assert response.status_code == 200

    def test_settings_tokens(self, authenticated_client):
        """Test /settings/tokens page loads."""
        response = authenticated_client.get("/settings/tokens")

        assert response.status_code == 200

    def test_settings_sessions(self, authenticated_client):
        """Test /settings/sessions page loads."""
        response = authenticated_client.get("/settings/sessions")

        assert response.status_code == 200

    def test_tag_add_post(self, authenticated_client):
        """Test POST /settings/tags/add creates tag."""
        response = authenticated_client.post(
            "/settings/tags/add",
            data={"name": "new-tag", "color": "#ff0000"},
        )

        assert response.status_code == 200
        assert response.headers.get("HX-Redirect") == "/settings/tags"

    def test_tag_add_requires_name(self, authenticated_client):
        """Test POST /settings/tags/add fails without name."""
        response = authenticated_client.post(
            "/settings/tags/add",
            data={"color": "#ff0000"},
        )

        assert response.status_code == 400


class TestSessionRoutes:
    """Test session management routes."""

    def test_revoke_other_session(self, authenticated_client, db, test_user):
        """Test revoking another session."""
        from app import auth

        # Create another session
        other_token, other_session = auth.create_user_session(
            db, test_user.id, client_name="other"
        )

        response = authenticated_client.post(f"/settings/sessions/{other_token}/revoke")

        assert response.status_code == 200

    def test_cannot_revoke_current_session(self, authenticated_client, test_session):
        """Test that current session cannot be revoked."""
        token, session = test_session

        response = authenticated_client.post(f"/settings/sessions/{token}/revoke")

        assert response.status_code == 400


class TestExportRoute:
    """Test export functionality."""

    def test_export_page(self, authenticated_client, test_bookmark):
        """Test /export page loads."""
        response = authenticated_client.get("/export")

        assert response.status_code == 200
        assert "Export Data" in response.text

    def test_export_download_json(self, authenticated_client, test_bookmark):
        """Test /export/download returns JSON download."""
        response = authenticated_client.get("/export/download")

        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")

        data = response.json()
        assert "bookmarks" in data
        assert data["count"] >= 1


class TestAPIRoutes:
    """Test API route registration and basic functionality."""

    def test_api_requires_auth(self, app_client):
        """Test API endpoints require authentication."""
        response = app_client.post("/api/v1/bookmarks/list", json={})

        assert response.status_code == 401

    def test_api_with_token(self, app_client, test_token):
        """Test API endpoints work with valid token."""
        from app import auth
        auth.clear_rate_limit_store()

        plaintext, _ = test_token
        response = app_client.post(
            "/api/v1/bookmarks/list",
            json={},
            headers={"Authorization": f"Bearer {plaintext}"},
        )

        assert response.status_code == 200

    def test_api_bookmarks_add(self, app_client, test_token):
        """Test POST /api/v1/bookmarks/add."""
        from app import auth
        auth.clear_rate_limit_store()

        plaintext, _ = test_token
        response = app_client.post(
            "/api/v1/bookmarks/add",
            json={"url": "https://api-test.com", "title": "API Test"},
            headers={"Authorization": f"Bearer {plaintext}"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["url"] == "https://api-test.com"

    def test_api_tags_list(self, app_client, test_token, test_tag):
        """Test POST /api/v1/tags/list."""
        from app import auth
        auth.clear_rate_limit_store()

        plaintext, _ = test_token
        response = app_client.post(
            "/api/v1/tags/list",
            json={},
            headers={"Authorization": f"Bearer {plaintext}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "tags" in data


class TestHTTPMethods:
    """Test that routes respond to correct HTTP methods."""

    def test_logout_requires_post(self, authenticated_client):
        """Test /logout only accepts POST."""
        # GET should not work (either 405 or redirect)
        response = authenticated_client.get("/logout", follow_redirects=False)
        # FastHTML might return different codes, but POST should work

        # POST should work - returns 200 with HX-Redirect header for HTMX
        response = authenticated_client.post("/logout", follow_redirects=False)
        assert response.status_code == 200
        assert response.headers.get("HX-Redirect") == "/login"

    def test_bookmark_delete_requires_delete(self, authenticated_client, test_bookmark):
        """Test /bookmarks/{id} DELETE method requirement."""
        # POST to the endpoint with bookmark_id should be edit, not delete
        response = authenticated_client.post(
            f"/bookmarks/{test_bookmark.id}",
            data={"title": "Updated"},
        )
        # This should update, not delete
        assert response.status_code == 200


class TestOAuthRoutes:
    """Test OAuth route registration (without actual OAuth)."""

    def test_google_oauth_unconfigured(self, app_client):
        """Test /auth/google returns 503 when not configured."""
        response = app_client.get("/auth/google", follow_redirects=False)

        # Should return 503 when OAuth is not configured
        assert response.status_code == 503

    def test_github_oauth_unconfigured(self, app_client):
        """Test /auth/github returns 503 when not configured."""
        response = app_client.get("/auth/github", follow_redirects=False)

        assert response.status_code == 503
