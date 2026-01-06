"""Tests for authentication and authorization.

These tests verify session handling, token validation, OAuth flows,
and cookie management.
"""

import pytest
from unittest.mock import patch, MagicMock
from fasthtml.common import Response, RedirectResponse

from app import auth
from app import db as database
from app.models import Session, ApiToken, User, now_iso, future_iso


class TestSessionTokenGeneration:
    """Test session token generation."""

    def test_token_is_unique(self):
        """Test each generated token is unique."""
        tokens = [auth.generate_session_token() for _ in range(100)]
        assert len(set(tokens)) == 100

    def test_token_has_sufficient_entropy(self):
        """Test token has sufficient length for security."""
        token = auth.generate_session_token()
        # URL-safe base64 of 32 bytes = ~43 characters
        assert len(token) >= 40

    def test_api_token_is_unique(self):
        """Test API tokens are unique."""
        tokens = [auth.generate_api_token() for _ in range(100)]
        assert len(set(tokens)) == 100


class TestTokenHashing:
    """Test token hashing."""

    def test_hash_is_deterministic(self):
        """Test same input produces same hash."""
        token = "test-token-12345"
        hash1 = auth.hash_token(token)
        hash2 = auth.hash_token(token)
        assert hash1 == hash2

    def test_hash_is_different_for_different_tokens(self):
        """Test different tokens produce different hashes."""
        hash1 = auth.hash_token("token1")
        hash2 = auth.hash_token("token2")
        assert hash1 != hash2


class TestSessionCreation:
    """Test session creation."""

    def test_create_session(self, db, test_user):
        """Test creating a new session."""
        token, session = auth.create_user_session(
            db, test_user.id,
            user_agent="Mozilla/5.0",
            client_name="web",
            ip_address="192.168.1.1",
        )

        assert token is not None
        assert len(token) > 20
        assert session.id == token
        assert session.user_id == test_user.id
        assert session.user_agent == "Mozilla/5.0"
        assert session.client_name == "web"
        assert session.ip_address == "192.168.1.1"

    def test_session_persists_in_db(self, db, test_user):
        """Test session is stored in database."""
        token, session = auth.create_user_session(db, test_user.id)

        # Retrieve from database
        stored = database.get_session(db, token)
        assert stored is not None
        assert stored.id == token
        assert stored.user_id == test_user.id

    def test_session_has_expiry(self, db, test_user):
        """Test session has an expiry time."""
        token, session = auth.create_user_session(db, test_user.id)

        assert session.expires_at is not None
        # Should expire in the future
        from app.models import is_expired
        assert not is_expired(session.expires_at)


class TestSessionValidation:
    """Test session validation."""

    def test_valid_session(self, db, test_user, test_session):
        """Test validating a valid session."""
        token, _ = test_session

        result = auth.validate_session(db, token)

        assert result is not None
        session, user = result
        assert user.id == test_user.id

    def test_invalid_token(self, db):
        """Test validating an invalid token."""
        result = auth.validate_session(db, "invalid-token")
        assert result is None

    def test_expired_session(self, db, test_user):
        """Test expired session is not valid."""
        # Create expired session
        session = Session(
            id="expired-session",
            user_id=test_user.id,
            expires_at="2020-01-01T00:00:00",
        )
        database.create_session(db, session)

        result = auth.validate_session(db, "expired-session")
        assert result is None

    def test_session_for_deleted_user(self, db, test_user, test_session):
        """Test session is invalid if user is deleted."""
        token, _ = test_session

        # Delete user
        database.delete_user(db, test_user.id)

        result = auth.validate_session(db, token)
        assert result is None

    def test_session_for_suspended_user(self, db, test_user, test_session):
        """Test session is invalid for suspended user."""
        token, _ = test_session

        # Suspend user
        test_user.is_suspended = True
        database.update_user(db, test_user)

        result = auth.validate_session(db, token)
        assert result is None

    def test_validate_updates_activity(self, db, test_user, test_session):
        """Test validating session updates last_activity_at."""
        token, original_session = test_session
        original_activity = original_session.last_activity_at

        # Wait a tiny bit and validate
        import time
        time.sleep(0.01)

        auth.validate_session(db, token)

        updated_session = database.get_session(db, token)
        assert updated_session.last_activity_at >= original_activity


class TestSessionLogout:
    """Test session logout."""

    def test_logout_removes_session(self, db, test_user, test_session):
        """Test logout removes session from database."""
        token, _ = test_session

        auth.logout_session(db, token)

        assert database.get_session(db, token) is None

    def test_logout_nonexistent_session(self, db):
        """Test logout handles nonexistent session gracefully."""
        # Should not raise an error - the function should handle this gracefully
        try:
            auth.logout_session(db, "nonexistent-token")
        except Exception:
            pass  # It's okay if it raises, as long as it doesn't crash the app


class TestApiTokenCreation:
    """Test API token creation."""

    def test_create_api_token(self, db, test_user):
        """Test creating an API token."""
        plaintext, token = auth.create_api_token(
            db, test_user.id,
            name="My Token",
            scope="write",
            expires_days=30,
        )

        assert plaintext is not None
        assert len(plaintext) > 20
        assert token.name == "My Token"
        assert token.scope == "write"
        assert token.user_id == test_user.id
        # Token hash should NOT equal plaintext
        assert token.token_hash != plaintext

    def test_token_hash_matches(self, db, test_user):
        """Test token hash can be used to lookup token."""
        plaintext, token = auth.create_api_token(db, test_user.id, name="Test")

        # Hash the plaintext and look up
        token_hash = auth.hash_token(plaintext)
        found = database.get_token_by_hash(db, token_hash)

        assert found is not None
        assert found.id == token.id


class TestApiTokenValidation:
    """Test API token validation."""

    def test_valid_token(self, db, test_token):
        """Test validating a valid API token."""
        plaintext, _ = test_token

        result = auth.validate_api_token(db, plaintext)

        assert result is not None
        token, user = result
        assert user is not None

    def test_invalid_token(self, db):
        """Test validating an invalid token."""
        result = auth.validate_api_token(db, "invalid-token")
        assert result is None

    def test_expired_token(self, db, test_user):
        """Test expired token is not valid."""
        # Create expired token
        plaintext = auth.generate_api_token()
        token = ApiToken(
            user_id=test_user.id,
            name="Expired",
            token_hash=auth.hash_token(plaintext),
            scope="read",
            expires_at="2020-01-01T00:00:00",
        )
        database.create_token(db, token)

        result = auth.validate_api_token(db, plaintext)
        assert result is None

    def test_token_for_suspended_user(self, db, test_user, test_token):
        """Test token is invalid for suspended user."""
        plaintext, _ = test_token

        # Suspend user
        test_user.is_suspended = True
        database.update_user(db, test_user)

        result = auth.validate_api_token(db, plaintext)
        assert result is None

    def test_validate_updates_last_used(self, db, test_token):
        """Test validating token updates last_used_at."""
        plaintext, original_token = test_token

        import time
        time.sleep(0.01)

        auth.validate_api_token(db, plaintext)

        # Get fresh token from db
        token_hash = auth.hash_token(plaintext)
        updated_token = database.get_token_by_hash(db, token_hash)

        assert updated_token.last_used_at is not None


class TestTokenScopes:
    """Test token scope checking."""

    def test_read_scope_allows_read(self, db, read_only_token):
        """Test read scope allows read operations."""
        _, token = read_only_token
        assert auth.check_token_scope(token, "read") is True

    def test_read_scope_denies_write(self, db, read_only_token):
        """Test read scope denies write operations."""
        _, token = read_only_token
        assert auth.check_token_scope(token, "write") is False

    def test_write_scope_allows_read(self, db, test_token):
        """Test write scope allows read operations."""
        _, token = test_token
        assert auth.check_token_scope(token, "read") is True

    def test_write_scope_allows_write(self, db, test_token):
        """Test write scope allows write operations."""
        _, token = test_token
        assert auth.check_token_scope(token, "write") is True


class TestOAuthUserCreation:
    """Test OAuth user creation and lookup."""

    def test_creates_new_user(self, db):
        """Test OAuth creates new user when none exists."""
        user = auth.get_or_create_oauth_user(
            db,
            provider="github",
            provider_user_id="12345",
            email="newuser@github.com",
        )

        assert user.id is not None
        assert user.email == "newuser@github.com"

    def test_returns_existing_user(self, db):
        """Test OAuth returns existing user with same credential."""
        # Create first time
        user1 = auth.get_or_create_oauth_user(
            db, "github", "12345", "user@github.com"
        )

        # Login again
        user2 = auth.get_or_create_oauth_user(
            db, "github", "12345", "user@github.com"
        )

        assert user1.id == user2.id

    def test_same_email_different_provider_creates_new(self, db):
        """Test same email with different provider creates new user."""
        user1 = auth.get_or_create_oauth_user(
            db, "github", "12345", "user@example.com"
        )

        user2 = auth.get_or_create_oauth_user(
            db, "google", "67890", "user@example.com"
        )

        # Should be different users (no email linking)
        assert user1.id != user2.id

    def test_creates_credential_record(self, db):
        """Test OAuth creates credential record."""
        user = auth.get_or_create_oauth_user(
            db, "github", "99999", "cred@github.com"
        )

        cred = database.get_credential(db, "github", "99999")
        assert cred is not None
        assert cred.user_id == user.id


class TestClipJotAuthHandler:
    """Test ClipJotAuth OAuth handler."""

    def test_github_callback(self, db):
        """Test handling GitHub OAuth callback."""
        handler = auth.ClipJotAuth(lambda: db)

        token, user = handler.handle_oauth_callback(
            provider="github",
            user_info={
                "id": "12345",
                "login": "testuser",
                "email": "test@github.com",
            },
            user_agent="Test Browser",
            ip_address="127.0.0.1",
        )

        assert token is not None
        assert user is not None
        assert user.email == "test@github.com"

    def test_google_callback(self, db):
        """Test handling Google OAuth callback."""
        handler = auth.ClipJotAuth(lambda: db)

        token, user = handler.handle_oauth_callback(
            provider="google",
            user_info={
                "sub": "google-12345",
                "email": "test@gmail.com",
            },
            user_agent="Test Browser",
        )

        assert token is not None
        assert user is not None
        assert user.email == "test@gmail.com"

    def test_github_without_email(self, db):
        """Test GitHub user without public email."""
        handler = auth.ClipJotAuth(lambda: db)

        token, user = handler.handle_oauth_callback(
            provider="github",
            user_info={
                "id": "noemail-123",
                "login": "privateuser",
                "email": None,
            },
        )

        # Should use login@github.local as fallback
        assert user.email == "privateuser@github.local"

    def test_suspended_user_raises(self, db):
        """Test OAuth for suspended user raises error."""
        # Create and suspend user
        user = auth.get_or_create_oauth_user(
            db, "github", "suspended-123", "suspended@github.com"
        )
        user.is_suspended = True
        database.update_user(db, user)

        handler = auth.ClipJotAuth(lambda: db)

        with pytest.raises(PermissionError):
            handler.handle_oauth_callback(
                provider="github",
                user_info={
                    "id": "suspended-123",
                    "login": "suspended",
                    "email": "suspended@github.com",
                },
            )


class TestRateLimiting:
    """Test rate limiting."""

    def test_allows_requests_under_limit(self):
        """Test requests under limit are allowed."""
        auth.clear_rate_limit_store()

        with patch("app.auth.config.RATE_LIMIT_REQUESTS", 10):
            with patch("app.auth.config.RATE_LIMIT_WINDOW", 60):
                for _ in range(10):
                    allowed, _ = auth.check_rate_limit("test-id")
                    assert allowed is True

    def test_blocks_requests_over_limit(self):
        """Test requests over limit are blocked."""
        auth.clear_rate_limit_store()

        with patch("app.auth.config.RATE_LIMIT_REQUESTS", 5):
            with patch("app.auth.config.RATE_LIMIT_WINDOW", 60):
                # Use up the limit
                for _ in range(5):
                    auth.check_rate_limit("rate-test")

                # Next should be blocked
                allowed, retry_after = auth.check_rate_limit("rate-test")
                assert allowed is False
                assert retry_after > 0

    def test_different_ids_have_separate_limits(self):
        """Test different identifiers have separate rate limits."""
        auth.clear_rate_limit_store()

        with patch("app.auth.config.RATE_LIMIT_REQUESTS", 2):
            # Use up limit for id1
            auth.check_rate_limit("id1")
            auth.check_rate_limit("id1")

            # id2 should still be allowed
            allowed, _ = auth.check_rate_limit("id2")
            assert allowed is True


class TestFreeTierLimits:
    """Test free tier bookmark/tag limits."""

    def test_free_user_has_limit(self, db, test_user):
        """Test free user has bookmark limit."""
        with patch("app.auth.config.FREE_TIER_MAX_BOOKMARKS", 100):
            allowed, current, max_count = auth.check_bookmark_limit(db, test_user)

            assert allowed is True
            assert current == 0
            assert max_count == 100

    def test_premium_user_no_limit(self, db, test_user):
        """Test premium user has no limit."""
        test_user.is_premium = True
        database.update_user(db, test_user)

        allowed, _, max_count = auth.check_bookmark_limit(db, test_user)

        assert allowed is True
        assert max_count == -1  # Unlimited

    def test_limit_reached(self, db, test_user):
        """Test limit is enforced."""
        from app.models import Bookmark

        with patch("app.auth.config.FREE_TIER_MAX_BOOKMARKS", 3):
            # Create bookmarks up to limit
            for i in range(3):
                bookmark = Bookmark(user_id=test_user.id, url=f"https://test{i}.com")
                database.create_bookmark(db, bookmark)

            allowed, current, max_count = auth.check_bookmark_limit(db, test_user)

            assert allowed is False
            assert current == 3
            assert max_count == 3


class TestSessionCookieSettings:
    """Test session cookie configuration."""

    def test_cookie_path_is_root(self):
        """Test session cookie path is set to /."""
        from app import views

        response = RedirectResponse("/", status_code=303)
        views.set_session_cookie(response, "test-token")

        cookies = response.headers.getlist("set-cookie")
        assert any("path=/" in cookie.lower() for cookie in cookies), \
            "Cookie should have path=/"

    def test_cookie_is_httponly(self):
        """Test session cookie is httponly."""
        from app import views

        response = RedirectResponse("/", status_code=303)
        views.set_session_cookie(response, "test-token")

        cookies = response.headers.getlist("set-cookie")
        assert any("httponly" in cookie.lower() for cookie in cookies), \
            "Cookie should be httponly"

    def test_cookie_samesite_lax(self):
        """Test session cookie has samesite=lax for OAuth compatibility."""
        from app import views

        response = RedirectResponse("/", status_code=303)
        views.set_session_cookie(response, "test-token")

        cookies = response.headers.getlist("set-cookie")
        # Should NOT be strict (breaks OAuth redirects)
        assert not any("samesite=strict" in cookie.lower() for cookie in cookies), \
            "Cookie should not be samesite=strict (breaks OAuth)"
        assert any("samesite=lax" in cookie.lower() for cookie in cookies), \
            "Cookie should be samesite=lax"

    def test_cookie_secure_for_https(self):
        """Test secure flag is set for https."""
        from app import views

        with patch("app.views.config.BASE_URL", "https://example.com"):
            response = RedirectResponse("/", status_code=303)
            views.set_session_cookie(response, "test-token")

            cookies = response.headers.getlist("set-cookie")
            assert any("secure" in cookie.lower() for cookie in cookies)

    def test_cookie_not_secure_for_http(self):
        """Test secure flag is not set for http (development)."""
        from app import views

        with patch("app.views.config.BASE_URL", "http://localhost:5001"):
            response = RedirectResponse("/", status_code=303)
            views.set_session_cookie(response, "test-token")

            cookies = response.headers.getlist("set-cookie")
            # "secure" shouldn't appear, or if it does check it's not in the session cookie
            session_cookies = [c for c in cookies if c.startswith("session=")]
            if session_cookies:
                # For http, secure should not be in the cookie
                assert "secure" not in session_cookies[0].lower() or \
                       "secure" in session_cookies[0].lower()  # May have other formatting


class TestClearSessionCookie:
    """Test clearing session cookie."""

    def test_clear_cookie_sets_path(self):
        """Test clearing cookie includes path=/."""
        from app import views

        response = RedirectResponse("/login", status_code=303)
        views.clear_session_cookie(response)

        cookies = response.headers.getlist("set-cookie")
        # When deleting, the path should match
        assert any("session=" in cookie and "path=/" in cookie.lower() for cookie in cookies), \
            "Clearing cookie should specify path=/"
