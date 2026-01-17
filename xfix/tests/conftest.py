"""Pytest fixtures for XFix tests."""

import json
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from api_client import Bookmark
from fetcher import TweetContent


@pytest.fixture
def sample_bookmark():
    """Sample bookmark needing enrichment."""
    return Bookmark(
        id=123,
        url="https://x.com/testuser/status/1234567890",
        title=None,
        comment=None,
        tags=[],
        client_name="chrome-extension",
        created_at="2024-01-15T10:30:00Z",
    )


@pytest.fixture
def sample_bookmark_with_title():
    """Sample bookmark with title but no comment."""
    return Bookmark(
        id=124,
        url="https://x.com/testuser/status/1234567891",
        title="Existing title",
        comment=None,
        tags=[],
        client_name="chrome-extension",
        created_at="2024-01-15T10:31:00Z",
    )


@pytest.fixture
def sample_tweet_content():
    """Sample tweet content."""
    return TweetContent(
        author="testuser",
        text="This is a sample tweet about AI and machine learning. It discusses the latest developments in the field.",
        url="https://x.com/testuser/status/1234567890",
    )


@pytest.fixture
def sample_html_with_meta():
    """Sample HTML response with OpenGraph meta tags."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta property="og:title" content="testuser on X: This is a sample tweet about AI">
        <meta property="og:description" content="This is a sample tweet about AI and machine learning. It discusses the latest developments in the field.">
    </head>
    <body></body>
    </html>
    """


@pytest.fixture
def sample_ollama_response():
    """Sample Ollama response."""
    return """TITLE: AI and ML developments discussed by testuser
SUMMARY: The tweet covers recent advancements in artificial intelligence and machine learning. The author shares insights on new developments. This reflects growing interest in AI technologies. The content is relevant to tech enthusiasts and researchers."""


@pytest.fixture
def state_file(tmp_path):
    """Temporary state file for testing."""
    return tmp_path / "state.json"


@pytest.fixture
def state_file_with_data(tmp_path):
    """State file with existing data."""
    state_path = tmp_path / "state.json"
    data = {
        "cursor": "12345",
        "last_updated": "2024-01-15T10:00:00Z",
        "retries": {
            "https://x.com/user/status/111": {
                "attempts": 2,
                "last_attempt": "2024-01-15T09:55:00Z",
                "error_type": "network",
                "bookmark_id": 111,
            }
        },
        "failed": [
            {
                "url": "https://x.com/user/status/222",
                "bookmark_id": 222,
                "attempts": 3,
                "last_error": "not_found",
                "failed_at": "2024-01-15T09:50:00Z",
            }
        ],
        "backoff": {
            "current_delay": 0,
            "fibonacci_index": 0,
        },
    }
    state_path.write_text(json.dumps(data))
    return state_path


@pytest.fixture
def mock_httpx_client():
    """Mock httpx AsyncClient."""
    return AsyncMock()


@pytest.fixture
def mock_ollama_client():
    """Mock Ollama client."""
    mock = MagicMock()
    mock.list.return_value = MagicMock(
        models=[MagicMock(model="qwen3:latest")]
    )
    return mock
