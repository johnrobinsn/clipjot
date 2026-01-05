"""Tests for API endpoints."""

import pytest
import json
from unittest.mock import MagicMock, patch
from app import api
from app import db as database
from app import auth


class MockRequest:
    """Mock request object for API tests."""

    def __init__(self, headers=None, body=None):
        self.headers = headers or {}
        self._body = body or b"{}"

    async def body(self):
        return self._body


class TestApiAuthentication:
    """Test API authentication middleware."""

    def test_missing_auth_header(self, db):
        """Test request without Authorization header."""
        request = MockRequest()

        token, user, error = api.get_api_auth(request, db)

        assert error is not None
        assert token is None
        assert user is None

    def test_invalid_auth_header_format(self, db):
        """Test request with invalid Authorization header format."""
        request = MockRequest(headers={"Authorization": "Basic abc123"})

        token, user, error = api.get_api_auth(request, db)

        assert error is not None

    def test_invalid_token(self, db):
        """Test request with invalid token."""
        request = MockRequest(headers={"Authorization": "Bearer invalid-token"})

        token, user, error = api.get_api_auth(request, db)

        assert error is not None

    def test_valid_token(self, db, test_token):
        """Test request with valid token."""
        plaintext, token_obj = test_token
        request = MockRequest(headers={"Authorization": f"Bearer {plaintext}"})

        # Clear rate limit store for clean test
        auth.clear_rate_limit_store()

        token, user, error = api.get_api_auth(request, db)

        assert error is None
        assert token is not None
        assert user is not None

    def test_suspended_user_token(self, db, test_user, test_token):
        """Test that suspended user's token is rejected."""
        plaintext, _ = test_token

        # Suspend the user
        test_user.is_suspended = True
        database.update_user(db, test_user)

        request = MockRequest(headers={"Authorization": f"Bearer {plaintext}"})
        auth.clear_rate_limit_store()

        token, user, error = api.get_api_auth(request, db)

        assert error is not None


class TestBookmarkApi:
    """Test bookmark API endpoints."""

    def test_add_bookmark(self, db, test_token):
        """Test adding a bookmark via API."""
        plaintext, _ = test_token
        request = MockRequest(headers={"Authorization": f"Bearer {plaintext}"})
        auth.clear_rate_limit_store()

        data = {
            "url": "https://newsite.com",
            "title": "New Site",
            "comment": "A new bookmark",
            "tags": ["tag1", "tag2"],
        }

        response = api.api_bookmarks_add(request, db, data)

        assert response.status_code == 201
        body = json.loads(response.body)
        assert body["url"] == "https://newsite.com"
        assert body["title"] == "New Site"
        assert len(body["tags"]) == 2

    def test_add_bookmark_missing_url(self, db, test_token):
        """Test adding bookmark without URL fails."""
        plaintext, _ = test_token
        request = MockRequest(headers={"Authorization": f"Bearer {plaintext}"})
        auth.clear_rate_limit_store()

        data = {"title": "No URL"}

        response = api.api_bookmarks_add(request, db, data)

        assert response.status_code == 400

    def test_add_bookmark_requires_write_scope(self, db, read_only_token):
        """Test that adding bookmark requires write scope."""
        plaintext, _ = read_only_token
        request = MockRequest(headers={"Authorization": f"Bearer {plaintext}"})
        auth.clear_rate_limit_store()

        data = {"url": "https://test.com"}

        response = api.api_bookmarks_add(request, db, data)

        assert response.status_code == 403

    def test_search_bookmarks(self, db, test_token, test_bookmark):
        """Test searching bookmarks via API."""
        plaintext, _ = test_token
        request = MockRequest(headers={"Authorization": f"Bearer {plaintext}"})
        auth.clear_rate_limit_store()

        data = {"query": "Example"}

        response = api.api_bookmarks_search(request, db, data)

        assert response.status_code == 200
        body = json.loads(response.body)
        assert len(body["bookmarks"]) == 1

    def test_search_with_read_only_token(self, db, read_only_token, test_bookmark):
        """Test that search works with read-only token."""
        plaintext, _ = read_only_token
        request = MockRequest(headers={"Authorization": f"Bearer {plaintext}"})
        auth.clear_rate_limit_store()

        data = {}

        response = api.api_bookmarks_search(request, db, data)

        assert response.status_code == 200

    def test_delete_bookmark(self, db, test_token, test_bookmark):
        """Test deleting a bookmark via API."""
        plaintext, _ = test_token
        request = MockRequest(headers={"Authorization": f"Bearer {plaintext}"})
        auth.clear_rate_limit_store()

        data = {"id": test_bookmark.id}

        response = api.api_bookmarks_delete(request, db, data)

        assert response.status_code == 200
        body = json.loads(response.body)
        assert body["deleted"] is True

        # Verify deletion
        assert database.get_bookmark_by_id(db, test_bookmark.id) is None

    def test_delete_other_users_bookmark(self, db, test_token):
        """Test that users can't delete other users' bookmarks."""
        plaintext, _ = test_token
        request = MockRequest(headers={"Authorization": f"Bearer {plaintext}"})
        auth.clear_rate_limit_store()

        # Create another user's bookmark
        other_user = database.create_user(db, "other@example.com")
        from app.models import Bookmark
        bookmark = Bookmark(user_id=other_user.id, url="https://other.com")
        bookmark = database.create_bookmark(db, bookmark)

        data = {"id": bookmark.id}

        response = api.api_bookmarks_delete(request, db, data)

        assert response.status_code == 404


class TestTagApi:
    """Test tag API endpoints."""

    def test_list_tags(self, db, test_token, test_tag):
        """Test listing tags via API."""
        plaintext, _ = test_token
        request = MockRequest(headers={"Authorization": f"Bearer {plaintext}"})
        auth.clear_rate_limit_store()

        response = api.api_tags_list(request, db, {})

        assert response.status_code == 200
        body = json.loads(response.body)
        assert len(body["tags"]) == 1
        assert body["tags"][0]["name"] == "test-tag"

    def test_create_tag(self, db, test_token):
        """Test creating a tag via API."""
        plaintext, _ = test_token
        request = MockRequest(headers={"Authorization": f"Bearer {plaintext}"})
        auth.clear_rate_limit_store()

        data = {"name": "new-tag", "color": "#ff0000"}

        response = api.api_tags_create(request, db, data)

        assert response.status_code == 201
        body = json.loads(response.body)
        assert body["name"] == "new-tag"
        assert body["color"] == "#ff0000"

    def test_create_duplicate_tag(self, db, test_token, test_tag):
        """Test that creating duplicate tag fails."""
        plaintext, _ = test_token
        request = MockRequest(headers={"Authorization": f"Bearer {plaintext}"})
        auth.clear_rate_limit_store()

        data = {"name": "test-tag"}

        response = api.api_tags_create(request, db, data)

        assert response.status_code == 400

    def test_delete_tag(self, db, test_token, test_tag):
        """Test deleting a tag via API."""
        plaintext, _ = test_token
        request = MockRequest(headers={"Authorization": f"Bearer {plaintext}"})
        auth.clear_rate_limit_store()

        data = {"id": test_tag.id}

        response = api.api_tags_delete(request, db, data)

        assert response.status_code == 200
        body = json.loads(response.body)
        assert body["deleted"] is True


class TestExportApi:
    """Test export API endpoint."""

    def test_export_bookmarks(self, db, test_token, test_bookmark, test_tag):
        """Test exporting bookmarks via API."""
        plaintext, _ = test_token
        request = MockRequest(headers={"Authorization": f"Bearer {plaintext}"})
        auth.clear_rate_limit_store()

        # Add tag to bookmark
        database.add_bookmark_tag(db, test_bookmark.id, test_tag.id)

        response = api.api_export(request, db, {})

        assert response.status_code == 200
        body = json.loads(response.body)
        assert body["count"] == 1
        assert len(body["bookmarks"]) == 1
        assert body["bookmarks"][0]["url"] == test_bookmark.url
        assert "test-tag" in body["bookmarks"][0]["tags"]


class TestRateLimiting:
    """Test API rate limiting."""

    def test_rate_limit_enforced(self, db, test_token):
        """Test that rate limiting is enforced."""
        plaintext, _ = test_token

        # Override rate limit for testing
        with patch("app.auth.config.RATE_LIMIT_REQUESTS", 5):
            with patch("app.auth.config.RATE_LIMIT_WINDOW", 60):
                auth.clear_rate_limit_store()

                # Make requests up to limit
                for i in range(5):
                    allowed, _ = auth.check_rate_limit(plaintext)
                    assert allowed is True

                # Next request should be rate limited
                allowed, retry_after = auth.check_rate_limit(plaintext)
                assert allowed is False
                assert retry_after > 0
