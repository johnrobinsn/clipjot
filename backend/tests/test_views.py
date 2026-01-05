"""Tests for view functions and HTML rendering.

These tests verify that views render correctly and handle edge cases.
"""

import pytest
from unittest.mock import MagicMock, patch
from fasthtml.common import Response

from app import views
from app import db as database
from app.models import Bookmark, Tag


class MockRequest:
    """Mock Starlette request for testing views."""

    def __init__(
        self,
        cookies=None,
        query_params=None,
        headers=None,
        client=None,
        form_data=None,
    ):
        self.cookies = cookies or {}
        self.query_params = query_params or {}
        self.headers = headers or {}
        self.client = client
        self._form_data = form_data or {}

    async def form(self):
        """Return mock form data."""
        return MockFormData(self._form_data)


class MockFormData(dict):
    """Mock form data with getlist support."""

    def getlist(self, key):
        value = self.get(key, [])
        if isinstance(value, list):
            return value
        return [value] if value else []


class TestGetCurrentUser:
    """Test session/user retrieval from cookies."""

    def test_no_session_cookie(self, db):
        """Test returns None when no session cookie."""
        request = MockRequest()

        result = views.get_current_user(request, db)

        assert result is None

    def test_invalid_session_cookie(self, db):
        """Test returns None for invalid session token."""
        request = MockRequest(cookies={"session": "invalid-token"})

        result = views.get_current_user(request, db)

        assert result is None

    def test_valid_session(self, db, test_user, test_session):
        """Test returns user for valid session."""
        token, session = test_session
        request = MockRequest(cookies={"session": token})

        result = views.get_current_user(request, db)

        assert result is not None
        user, session_token = result
        assert user.id == test_user.id
        assert session_token == token

    def test_expired_session(self, db, test_user):
        """Test returns None for expired session."""
        from app.models import Session

        # Create expired session
        session = Session(
            id="expired-token",
            user_id=test_user.id,
            expires_at="2020-01-01T00:00:00",
        )
        database.create_session(db, session)

        request = MockRequest(cookies={"session": "expired-token"})

        result = views.get_current_user(request, db)

        assert result is None

    def test_suspended_user_session(self, db, test_user, test_session):
        """Test returns None for suspended user's session."""
        token, session = test_session

        # Suspend user
        test_user.is_suspended = True
        database.update_user(db, test_user)

        request = MockRequest(cookies={"session": token})

        result = views.get_current_user(request, db)

        assert result is None


class TestRequireAuth:
    """Test authentication requirement decorator."""

    def test_redirects_without_auth(self, db):
        """Test redirects to login without authentication."""
        request = MockRequest()

        result = views.require_auth(request, db)

        assert isinstance(result, Response)
        assert result.status_code == 303

    def test_returns_user_with_auth(self, db, test_user, test_session):
        """Test returns user tuple with valid auth."""
        token, session = test_session
        request = MockRequest(cookies={"session": token})

        result = views.require_auth(request, db)

        assert not isinstance(result, Response)
        user, session_token = result
        assert user.id == test_user.id


class TestLoginPage:
    """Test login page rendering."""

    def test_login_page_renders(self, db):
        """Test login page renders without error."""
        request = MockRequest()

        with patch("app.views.config.has_google_oauth", return_value=False):
            with patch("app.views.config.has_github_oauth", return_value=True):
                response = views.login_page(request, db)

        # Should return HTML (tuple of FT elements), not a redirect
        assert not isinstance(response, Response) or response.status_code != 303

    def test_login_redirects_if_authenticated(self, db, test_user, test_session):
        """Test login page redirects if already authenticated."""
        token, session = test_session
        request = MockRequest(cookies={"session": token})

        response = views.login_page(request, db)

        assert isinstance(response, Response)
        assert response.status_code == 303


class TestBookmarkIndex:
    """Test bookmark listing page."""

    def test_empty_bookmark_list(self, db, test_user, test_session):
        """Test index renders with no bookmarks."""
        token, _ = test_session
        request = MockRequest(cookies={"session": token})

        response = views.bookmark_index(request, db)

        # Should return HTML content (tuple), not a redirect
        assert not isinstance(response, Response) or response.status_code == 200

    def test_bookmark_list_with_items(self, db, test_user, test_session, test_bookmark):
        """Test index renders with bookmarks."""
        token, _ = test_session
        request = MockRequest(cookies={"session": token})

        response = views.bookmark_index(request, db)

        # Should return HTML content (tuple), not a redirect
        assert not isinstance(response, Response) or response.status_code == 200

    def test_bookmark_search(self, db, test_user, test_session, test_bookmark):
        """Test search query filtering."""
        token, _ = test_session
        request = MockRequest(
            cookies={"session": token},
            query_params={"q": "Example"},
        )

        response = views.bookmark_index(request, db)

        # Should return HTML content, not a redirect
        assert not isinstance(response, Response) or response.status_code == 200

    def test_bookmark_pagination(self, db, test_user, test_session):
        """Test pagination parameters."""
        token, _ = test_session

        # Create multiple bookmarks
        for i in range(60):
            bookmark = Bookmark(
                user_id=test_user.id,
                url=f"https://example{i}.com",
                title=f"Example {i}",
            )
            database.create_bookmark(db, bookmark)

        request = MockRequest(
            cookies={"session": token},
            query_params={"page": "2"},
        )

        response = views.bookmark_index(request, db)

        # Should return HTML content, not a redirect
        assert not isinstance(response, Response) or response.status_code == 200


class TestBookmarkAdd:
    """Test adding bookmarks."""

    @pytest.mark.asyncio
    async def test_add_bookmark_success(self, db, test_user, test_session):
        """Test successfully adding a bookmark."""
        token, _ = test_session
        request = MockRequest(
            cookies={"session": token},
            form_data={"url": "https://newsite.com", "title": "New Site"},
        )

        response = await views.bookmark_add(request, db)

        assert response.status_code == 200
        assert response.headers.get("HX-Redirect") == "/"

        # Verify bookmark was created
        bookmarks = database.get_user_bookmarks(db, test_user.id)
        assert len(bookmarks) == 1
        assert bookmarks[0].url == "https://newsite.com"

    @pytest.mark.asyncio
    async def test_add_bookmark_missing_url(self, db, test_user, test_session):
        """Test adding bookmark fails without URL."""
        token, _ = test_session
        request = MockRequest(
            cookies={"session": token},
            form_data={"title": "No URL"},
        )

        response = await views.bookmark_add(request, db)

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_add_bookmark_with_tags(self, db, test_user, test_session, test_tag):
        """Test adding bookmark with tags."""
        token, _ = test_session
        request = MockRequest(
            cookies={"session": token},
            form_data={
                "url": "https://tagged.com",
                "title": "Tagged Site",
                "tags": [str(test_tag.id)],
            },
        )

        response = await views.bookmark_add(request, db)

        assert response.status_code == 200

        # Verify tags were added
        bookmarks = database.get_user_bookmarks(db, test_user.id)
        tags = database.get_bookmark_tags(db, bookmarks[0].id)
        assert len(tags) == 1


class TestBookmarkDelete:
    """Test deleting bookmarks."""

    def test_delete_bookmark_success(self, db, test_user, test_session, test_bookmark):
        """Test successfully deleting a bookmark."""
        token, _ = test_session
        request = MockRequest(cookies={"session": token})

        response = views.bookmark_delete(request, db, test_bookmark.id)

        assert response.status_code == 200

        # Verify deletion
        assert database.get_bookmark_by_id(db, test_bookmark.id) is None

    def test_delete_other_users_bookmark(self, db, test_user, test_session):
        """Test cannot delete another user's bookmark."""
        token, _ = test_session

        # Create another user's bookmark
        other_user = database.create_user(db, "other@example.com")
        bookmark = Bookmark(user_id=other_user.id, url="https://other.com")
        bookmark = database.create_bookmark(db, bookmark)

        request = MockRequest(cookies={"session": token})

        response = views.bookmark_delete(request, db, bookmark.id)

        assert response.status_code == 404

    def test_delete_nonexistent_bookmark(self, db, test_user, test_session):
        """Test deleting nonexistent bookmark returns 404."""
        token, _ = test_session
        request = MockRequest(cookies={"session": token})

        response = views.bookmark_delete(request, db, 99999)

        assert response.status_code == 404


class TestBulkDelete:
    """Test bulk bookmark deletion."""

    @pytest.mark.asyncio
    async def test_bulk_delete(self, db, test_user, test_session):
        """Test bulk deleting bookmarks."""
        token, _ = test_session

        # Create multiple bookmarks
        bookmark_ids = []
        for i in range(3):
            bookmark = Bookmark(
                user_id=test_user.id,
                url=f"https://bulk{i}.com",
            )
            bookmark = database.create_bookmark(db, bookmark)
            bookmark_ids.append(str(bookmark.id))

        request = MockRequest(
            cookies={"session": token},
            form_data={"selected": bookmark_ids},
        )

        response = await views.bookmark_bulk_delete(request, db)

        assert response.status_code == 200
        assert response.headers.get("HX-Redirect") == "/"

        # Verify all deleted
        for bid in bookmark_ids:
            assert database.get_bookmark_by_id(db, int(bid)) is None


class TestTagManagement:
    """Test tag management views."""

    @pytest.mark.asyncio
    async def test_create_tag(self, db, test_user, test_session):
        """Test creating a new tag."""
        token, _ = test_session
        request = MockRequest(
            cookies={"session": token},
            form_data={"name": "new-tag", "color": "#ff0000"},
        )

        response = await views.settings_tag_add(request, db)

        assert response.status_code == 200

        # Verify tag was created
        tag = database.get_tag_by_name(db, test_user.id, "new-tag")
        assert tag is not None
        assert tag.color == "#ff0000"

    @pytest.mark.asyncio
    async def test_create_duplicate_tag(self, db, test_user, test_session, test_tag):
        """Test creating duplicate tag fails."""
        token, _ = test_session
        request = MockRequest(
            cookies={"session": token},
            form_data={"name": test_tag.name},
        )

        response = await views.settings_tag_add(request, db)

        assert response.status_code == 400

    def test_delete_tag(self, db, test_user, test_session, test_tag):
        """Test deleting a tag."""
        token, _ = test_session
        request = MockRequest(cookies={"session": token})

        response = views.settings_tag_delete(request, db, test_tag.id)

        assert response.status_code == 200

        # Verify deletion
        assert database.get_tag_by_id(db, test_tag.id) is None


class TestSessionManagement:
    """Test session management views."""

    def test_revoke_other_session(self, db, test_user, test_session):
        """Test revoking another session."""
        current_token, _ = test_session

        # Create another session
        from app import auth
        other_token, _ = auth.create_user_session(db, test_user.id)

        request = MockRequest(cookies={"session": current_token})

        response = views.settings_session_revoke(request, db, other_token)

        assert response.status_code == 200

        # Verify other session is revoked
        assert database.get_session(db, other_token) is None

        # Current session should still exist
        assert database.get_session(db, current_token) is not None

    def test_cannot_revoke_current_session(self, db, test_user, test_session):
        """Test that current session cannot be revoked via single revoke."""
        current_token, _ = test_session
        request = MockRequest(cookies={"session": current_token})

        response = views.settings_session_revoke(request, db, current_token)

        assert response.status_code == 400


class TestExport:
    """Test data export."""

    def test_export_bookmarks(self, db, test_user, test_session, test_bookmark, test_tag):
        """Test exporting user bookmarks."""
        token, _ = test_session

        # Add tag to bookmark
        database.add_bookmark_tag(db, test_bookmark.id, test_tag.id)

        request = MockRequest(cookies={"session": token})

        response = views.export_page(request, db)

        assert response.status_code == 200
        assert "application/json" in response.media_type

    def test_export_with_many_bookmarks(self, db, test_user, test_session):
        """Test export handles many bookmarks (pagination)."""
        token, _ = test_session

        # Create many bookmarks
        for i in range(150):
            bookmark = Bookmark(
                user_id=test_user.id,
                url=f"https://example{i}.com",
            )
            database.create_bookmark(db, bookmark)

        request = MockRequest(cookies={"session": token})

        response = views.export_page(request, db)

        assert response.status_code == 200
        import json
        data = json.loads(response.body)
        assert data["count"] == 150


class TestOAuthCallback:
    """Test OAuth callback handling."""

    def test_oauth_callback_creates_session(self, db):
        """Test OAuth callback creates user and session."""
        request = MockRequest(
            headers={"user-agent": "Test Browser"},
            client=MagicMock(host="127.0.0.1"),
        )

        user_info = {
            "id": "12345",
            "login": "testuser",
            "email": "testuser@github.com",
        }

        response = views.oauth_callback_handler(request, db, "github", user_info)

        # Should be a redirect with session cookie
        assert response.status_code == 303
        # Check that Set-Cookie header is present
        cookies = response.headers.getlist("set-cookie")
        assert any("session=" in cookie for cookie in cookies)

    def test_oauth_callback_suspended_user(self, db):
        """Test OAuth callback rejects suspended user."""
        # Create a suspended user with matching credential
        from app import auth as auth_module
        user = database.create_user(db, "suspended@github.com")
        user.is_suspended = True
        database.update_user(db, user)
        database.create_credential(db, user.id, "github", "99999")

        request = MockRequest(
            headers={"user-agent": "Test Browser"},
            client=MagicMock(host="127.0.0.1"),
        )

        user_info = {
            "id": "99999",
            "login": "suspendeduser",
            "email": "suspended@github.com",
        }

        response = views.oauth_callback_handler(request, db, "github", user_info)

        # Should show error page, not redirect
        assert not isinstance(response, Response) or response.status_code != 303


class TestFreeTierLimits:
    """Test free tier limitations."""

    @pytest.mark.asyncio
    async def test_bookmark_limit_reached(self, db, test_user, test_session):
        """Test bookmark creation fails when limit reached."""
        token, _ = test_session

        # Create bookmarks up to limit
        with patch("app.auth.config.FREE_TIER_MAX_BOOKMARKS", 5):
            for i in range(5):
                bookmark = Bookmark(
                    user_id=test_user.id,
                    url=f"https://limit{i}.com",
                )
                database.create_bookmark(db, bookmark)

            # Try to add one more
            request = MockRequest(
                cookies={"session": token},
                form_data={"url": "https://toomany.com"},
            )

            response = await views.bookmark_add(request, db)

            assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_premium_user_no_limit(self, db, test_session):
        """Test premium user has no bookmark limit."""
        token, session = test_session

        # Get user and make premium
        session_obj = database.get_session(db, token)
        user = database.get_user_by_id(db, session_obj.user_id)
        user.is_premium = True
        database.update_user(db, user)

        with patch("app.auth.config.FREE_TIER_MAX_BOOKMARKS", 5):
            # Create more than free limit
            for i in range(6):
                bookmark = Bookmark(
                    user_id=user.id,
                    url=f"https://premium{i}.com",
                )
                database.create_bookmark(db, bookmark)

            # Should still be able to add
            request = MockRequest(
                cookies={"session": token},
                form_data={"url": "https://moremore.com"},
            )

            response = await views.bookmark_add(request, db)

            assert response.status_code == 200
