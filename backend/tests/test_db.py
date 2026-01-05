"""Tests for database operations."""

import pytest
from app import db as database
from app.models import Bookmark, Tag, User, now_iso


class TestUserOperations:
    """Test user CRUD operations."""

    def test_create_user(self, db):
        """Test creating a new user."""
        user = database.create_user(db, "newuser@example.com")

        assert user.id is not None
        assert user.email == "newuser@example.com"
        assert user.created_at is not None
        assert user.is_premium is False
        assert user.is_admin is False

    def test_get_user_by_id(self, db, test_user):
        """Test getting user by ID."""
        user = database.get_user_by_id(db, test_user.id)

        assert user is not None
        assert user.id == test_user.id
        assert user.email == test_user.email

    def test_get_user_by_email(self, db, test_user):
        """Test getting user by email."""
        user = database.get_user_by_email(db, test_user.email)

        assert user is not None
        assert user.id == test_user.id

    def test_get_nonexistent_user(self, db):
        """Test getting a user that doesn't exist."""
        user = database.get_user_by_id(db, 99999)
        assert user is None

        user = database.get_user_by_email(db, "nonexistent@example.com")
        assert user is None

    def test_delete_user_cascades(self, db, test_user, test_bookmark, test_tag):
        """Test that deleting a user cascades to related data."""
        # Add tag to bookmark
        database.add_bookmark_tag(db, test_bookmark.id, test_tag.id)

        # Create a session
        from app import auth
        auth.create_user_session(db, test_user.id)

        # Delete user
        database.delete_user(db, test_user.id)

        # Verify cascade
        assert database.get_user_by_id(db, test_user.id) is None
        assert database.get_bookmark_by_id(db, test_bookmark.id) is None
        assert database.get_tag_by_id(db, test_tag.id) is None


class TestBookmarkOperations:
    """Test bookmark CRUD operations."""

    def test_create_bookmark(self, db, test_user):
        """Test creating a bookmark."""
        bookmark = Bookmark(
            user_id=test_user.id,
            url="https://test.com",
            title="Test",
        )
        bookmark = database.create_bookmark(db, bookmark)

        assert bookmark.id is not None
        assert bookmark.url == "https://test.com"
        assert bookmark.created_at is not None

    def test_search_bookmarks_by_title(self, db, test_user, test_bookmark):
        """Test searching bookmarks by title."""
        results = database.search_bookmarks(db, test_user.id, "Example")

        assert len(results) == 1
        assert results[0].id == test_bookmark.id

    def test_search_bookmarks_by_url(self, db, test_user, test_bookmark):
        """Test searching bookmarks by URL."""
        results = database.search_bookmarks(db, test_user.id, "example.com")

        assert len(results) == 1
        assert results[0].id == test_bookmark.id

    def test_search_bookmarks_by_comment(self, db, test_user, test_bookmark):
        """Test searching bookmarks by comment."""
        results = database.search_bookmarks(db, test_user.id, "test bookmark")

        assert len(results) == 1
        assert results[0].id == test_bookmark.id

    def test_search_bookmarks_no_results(self, db, test_user, test_bookmark):
        """Test searching with no matching results."""
        results = database.search_bookmarks(db, test_user.id, "nonexistent")

        assert len(results) == 0

    def test_search_bookmarks_empty_query(self, db, test_user, test_bookmark):
        """Test searching with empty query returns all bookmarks."""
        results = database.search_bookmarks(db, test_user.id, "")

        assert len(results) == 1

    def test_count_user_bookmarks(self, db, test_user, test_bookmark):
        """Test counting user bookmarks."""
        count = database.count_user_bookmarks(db, test_user.id)
        assert count == 1

        # Add another bookmark
        bookmark2 = Bookmark(user_id=test_user.id, url="https://test2.com")
        database.create_bookmark(db, bookmark2)

        count = database.count_user_bookmarks(db, test_user.id)
        assert count == 2

    def test_delete_bookmark(self, db, test_user, test_bookmark, test_tag):
        """Test deleting a bookmark removes tag associations."""
        database.add_bookmark_tag(db, test_bookmark.id, test_tag.id)

        database.delete_bookmark(db, test_bookmark.id)

        assert database.get_bookmark_by_id(db, test_bookmark.id) is None
        # Tag should still exist
        assert database.get_tag_by_id(db, test_tag.id) is not None


class TestTagOperations:
    """Test tag CRUD operations."""

    def test_create_tag(self, db, test_user):
        """Test creating a tag."""
        tag = database.create_tag(db, test_user.id, "new-tag", "#ff0000")

        assert tag.id is not None
        assert tag.name == "new-tag"
        assert tag.color == "#ff0000"

    def test_get_tag_by_name(self, db, test_user, test_tag):
        """Test getting tag by name."""
        tag = database.get_tag_by_name(db, test_user.id, "test-tag")

        assert tag is not None
        assert tag.id == test_tag.id

    def test_delete_tag_cascades(self, db, test_user, test_bookmark, test_tag):
        """Test that deleting a tag removes it from bookmarks."""
        database.add_bookmark_tag(db, test_bookmark.id, test_tag.id)

        # Verify tag is associated
        tags = database.get_bookmark_tags(db, test_bookmark.id)
        assert len(tags) == 1

        # Delete tag
        database.delete_tag(db, test_tag.id)

        # Verify tag is removed from bookmark
        tags = database.get_bookmark_tags(db, test_bookmark.id)
        assert len(tags) == 0

        # Bookmark should still exist
        assert database.get_bookmark_by_id(db, test_bookmark.id) is not None

    def test_get_tags_with_counts(self, db, test_user, test_bookmark, test_tag):
        """Test getting tags with bookmark counts."""
        database.add_bookmark_tag(db, test_bookmark.id, test_tag.id)

        tags = database.get_tags_with_counts(db, test_user.id)

        assert len(tags) == 1
        assert tags[0]["name"] == "test-tag"
        assert tags[0]["bookmark_count"] == 1


class TestBookmarkTagOperations:
    """Test bookmark-tag relationship operations."""

    def test_add_bookmark_tag(self, db, test_bookmark, test_tag):
        """Test adding a tag to a bookmark."""
        database.add_bookmark_tag(db, test_bookmark.id, test_tag.id)

        tags = database.get_bookmark_tags(db, test_bookmark.id)
        assert len(tags) == 1
        assert tags[0].id == test_tag.id

    def test_set_bookmark_tags(self, db, test_user, test_bookmark, test_tag):
        """Test setting multiple tags on a bookmark."""
        tag2 = database.create_tag(db, test_user.id, "tag2")

        database.set_bookmark_tags(db, test_bookmark.id, [test_tag.id, tag2.id])

        tags = database.get_bookmark_tags(db, test_bookmark.id)
        assert len(tags) == 2

        # Replace with different tags
        tag3 = database.create_tag(db, test_user.id, "tag3")
        database.set_bookmark_tags(db, test_bookmark.id, [tag3.id])

        tags = database.get_bookmark_tags(db, test_bookmark.id)
        assert len(tags) == 1
        assert tags[0].id == tag3.id

    def test_remove_bookmark_tag(self, db, test_bookmark, test_tag):
        """Test removing a tag from a bookmark."""
        database.add_bookmark_tag(db, test_bookmark.id, test_tag.id)
        database.remove_bookmark_tag(db, test_bookmark.id, test_tag.id)

        tags = database.get_bookmark_tags(db, test_bookmark.id)
        assert len(tags) == 0


class TestSessionOperations:
    """Test session operations."""

    def test_create_session(self, db, test_user):
        """Test creating a session."""
        from app import auth

        token, session = auth.create_user_session(
            db, test_user.id,
            user_agent="Test Browser",
            client_name="web",
        )

        assert token is not None
        assert len(token) > 20
        assert session.user_id == test_user.id

    def test_get_session(self, db, test_session):
        """Test getting a valid session."""
        token, session = test_session

        retrieved = database.get_session(db, token)
        assert retrieved is not None
        assert retrieved.id == token

    def test_expired_session_returns_none(self, db, test_user):
        """Test that expired sessions are not returned."""
        from app.models import Session, future_iso

        # Create an expired session
        session = Session(
            id="expired-token",
            user_id=test_user.id,
            expires_at="2020-01-01T00:00:00",  # Past date
        )
        database.create_session(db, session)

        # Should return None for expired session
        retrieved = database.get_session(db, "expired-token")
        assert retrieved is None

    def test_cleanup_expired_sessions(self, db, test_user):
        """Test cleaning up expired sessions."""
        from app.models import Session

        # Create expired sessions
        for i in range(3):
            session = Session(
                id=f"expired-{i}",
                user_id=test_user.id,
                expires_at="2020-01-01T00:00:00",
            )
            database.create_session(db, session)

        count = database.cleanup_expired_sessions(db)
        assert count == 3
