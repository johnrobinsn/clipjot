"""Pytest fixtures for ClipJot tests."""

import os
import sys
import pytest
from unittest.mock import patch

# Add backend to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure pytest-asyncio
pytest_plugins = ('pytest_asyncio',)


@pytest.fixture
def db():
    """Create an in-memory test database."""
    from fastlite import database
    from app.db import init_db

    # Create in-memory database
    test_db = database(":memory:")
    init_db(test_db)

    yield test_db


@pytest.fixture
def test_user(db):
    """Create a test user."""
    from app import db as database

    user = database.create_user(db, "test@example.com")
    return user


@pytest.fixture
def admin_user(db):
    """Create a test admin user."""
    from app import db as database

    user = database.create_user(db, "admin@example.com")
    user.is_admin = True
    user = database.update_user(db, user)
    return user


@pytest.fixture
def test_token(db, test_user):
    """Create a test API token with write scope."""
    from app import auth

    plaintext, token = auth.create_api_token(
        db,
        test_user.id,
        name="Test Token",
        scope="write",
        expires_days=30,
    )
    return plaintext, token


@pytest.fixture
def read_only_token(db, test_user):
    """Create a test API token with read-only scope."""
    from app import auth

    plaintext, token = auth.create_api_token(
        db,
        test_user.id,
        name="Read Only Token",
        scope="read",
        expires_days=30,
    )
    return plaintext, token


@pytest.fixture
def test_session(db, test_user):
    """Create a test session."""
    from app import auth

    token, session = auth.create_user_session(
        db,
        test_user.id,
        user_agent="Test Browser",
        client_name="web",
        ip_address="127.0.0.1",
    )
    return token, session


@pytest.fixture
def test_tag(db, test_user):
    """Create a test tag."""
    from app import db as database

    tag = database.create_tag(db, test_user.id, "test-tag")
    return tag


@pytest.fixture
def test_bookmark(db, test_user):
    """Create a test bookmark."""
    from app.models import Bookmark
    from app import db as database

    bookmark = Bookmark(
        user_id=test_user.id,
        url="https://example.com",
        title="Example Site",
        comment="A test bookmark",
        client_name="test",
    )
    bookmark = database.create_bookmark(db, bookmark)
    return bookmark


@pytest.fixture
def mock_config():
    """Mock configuration for tests."""
    with patch.multiple(
        "app.config",
        SECRET_KEY="test-secret-key",
        DATABASE_PATH=":memory:",
        BASE_URL="http://localhost:5001",
        GOOGLE_CLIENT_ID=None,
        GOOGLE_CLIENT_SECRET=None,
        GITHUB_CLIENT_ID=None,
        GITHUB_CLIENT_SECRET=None,
        RATE_LIMIT_REQUESTS=100,
        RATE_LIMIT_WINDOW=60,
        SESSION_MAX_AGE=2592000,
        FREE_TIER_MAX_BOOKMARKS=1000,
        FREE_TIER_MAX_TAGS=50,
    ):
        yield
