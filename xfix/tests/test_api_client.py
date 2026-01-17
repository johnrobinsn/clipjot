"""Tests for ClipJot API client."""

import pytest

from api_client import Bookmark, is_x_url, needs_enrichment


class TestIsXUrl:
    """Tests for X.com URL detection."""

    def test_x_com_basic(self):
        assert is_x_url("https://x.com/user/status/123") is True

    def test_x_com_www(self):
        assert is_x_url("https://www.x.com/user/status/123") is True

    def test_twitter_com_basic(self):
        assert is_x_url("https://twitter.com/user/status/123") is True

    def test_twitter_com_www(self):
        assert is_x_url("https://www.twitter.com/user/status/123") is True

    def test_mobile_twitter(self):
        assert is_x_url("https://mobile.twitter.com/user/status/123") is True

    def test_m_twitter(self):
        assert is_x_url("https://m.twitter.com/user/status/123") is True

    def test_http_scheme(self):
        assert is_x_url("http://x.com/user/status/123") is True

    def test_other_domain(self):
        assert is_x_url("https://example.com/page") is False

    def test_x_in_path(self):
        # Should not match x.com in path
        assert is_x_url("https://example.com/x.com/page") is False


class TestNeedsEnrichment:
    """Tests for enrichment detection."""

    def test_both_empty(self):
        bookmark = Bookmark(
            id=1, url="https://x.com/a", title=None, comment=None,
            tags=[], client_name=None, created_at=""
        )
        assert needs_enrichment(bookmark) is True

    def test_title_empty(self):
        bookmark = Bookmark(
            id=1, url="https://x.com/a", title=None, comment="Has comment",
            tags=[], client_name=None, created_at=""
        )
        assert needs_enrichment(bookmark) is True

    def test_comment_empty(self):
        bookmark = Bookmark(
            id=1, url="https://x.com/a", title="Has title", comment=None,
            tags=[], client_name=None, created_at=""
        )
        assert needs_enrichment(bookmark) is True

    def test_both_filled(self):
        bookmark = Bookmark(
            id=1, url="https://x.com/a", title="Has title", comment="Has comment",
            tags=[], client_name=None, created_at=""
        )
        assert needs_enrichment(bookmark) is False

    def test_empty_strings(self):
        bookmark = Bookmark(
            id=1, url="https://x.com/a", title="", comment="",
            tags=[], client_name=None, created_at=""
        )
        # Empty strings are falsy, so should need enrichment
        assert needs_enrichment(bookmark) is True
