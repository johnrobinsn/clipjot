"""Tests for X.com content fetcher."""

import pytest

from fetcher import (
    RateLimiter,
    extract_author,
    extract_tweet_id,
    parse_tweet_from_html,
)


class TestExtractTweetId:
    """Tests for tweet ID extraction."""

    def test_basic_url(self):
        assert extract_tweet_id("https://x.com/user/status/1234567890") == "1234567890"

    def test_twitter_url(self):
        assert extract_tweet_id("https://twitter.com/user/status/9876543210") == "9876543210"

    def test_url_with_query(self):
        assert extract_tweet_id("https://x.com/user/status/123?s=20") == "123"

    def test_no_status(self):
        assert extract_tweet_id("https://x.com/user/followers") is None


class TestExtractAuthor:
    """Tests for author extraction."""

    def test_x_com(self):
        assert extract_author("https://x.com/testuser/status/123") == "testuser"

    def test_twitter_com(self):
        assert extract_author("https://twitter.com/otheruser/status/456") == "otheruser"

    def test_www_prefix(self):
        assert extract_author("https://www.x.com/myuser/status/789") == "myuser"

    def test_no_status(self):
        assert extract_author("https://x.com/user/followers") is None


class TestParseTweetFromHtml:
    """Tests for HTML parsing."""

    def test_og_description(self, sample_html_with_meta):
        result = parse_tweet_from_html(
            sample_html_with_meta,
            "https://x.com/testuser/status/123"
        )
        assert result is not None
        assert result.author == "testuser"
        assert "AI and machine learning" in result.text

    def test_html_entity_decoding(self):
        html = '''<meta property="og:description" content="Test &amp; &quot;quoted&quot; text">'''
        result = parse_tweet_from_html(html, "https://x.com/user/status/1")
        assert result is not None
        assert result.text == 'Test & "quoted" text'

    def test_og_title_fallback(self):
        html = '''<meta property="og:title" content="user on X: This is the tweet text from title">'''
        result = parse_tweet_from_html(html, "https://x.com/user/status/1")
        assert result is not None
        assert "tweet text from title" in result.text

    def test_no_meta_tags(self):
        html = "<html><body>No meta tags</body></html>"
        result = parse_tweet_from_html(html, "https://x.com/user/status/1")
        assert result is None

    def test_short_content(self):
        # Content less than 10 chars should be rejected
        html = '''<meta property="og:description" content="Short">'''
        result = parse_tweet_from_html(html, "https://x.com/user/status/1")
        assert result is None


class TestRateLimiter:
    """Tests for rate limiter with Fibonacci backoff."""

    def test_initial_state(self):
        rl = RateLimiter(min_delay=10, max_delay=60, max_backoff=3600)
        assert rl.get_current_delay() >= 10
        assert rl.get_current_delay() <= 60

    def test_normal_delay_range(self):
        rl = RateLimiter(min_delay=10, max_delay=60, max_backoff=3600)
        delays = [rl.get_normal_delay() for _ in range(100)]
        assert all(10 <= d <= 60 for d in delays)

    def test_backoff_sequence(self):
        rl = RateLimiter(min_delay=10, max_delay=60, max_backoff=3600)
        base = rl.base_delay  # 35

        # First error
        delay1 = rl.record_error()
        assert delay1 == base * 1  # 35

        # Second error
        delay2 = rl.record_error()
        assert delay2 == base * 1  # 35 (fib[1])

        # Third error
        delay3 = rl.record_error()
        assert delay3 == base * 2  # 70 (fib[2])

        # Fourth error
        delay4 = rl.record_error()
        assert delay4 == base * 3  # 105 (fib[3])

    def test_backoff_max_cap(self):
        rl = RateLimiter(min_delay=10, max_delay=60, max_backoff=100)
        base = rl.base_delay  # 35

        # Keep incrementing until we hit max
        for _ in range(20):
            delay = rl.record_error()
            assert delay <= 100

    def test_success_resets_backoff(self):
        rl = RateLimiter(min_delay=10, max_delay=60, max_backoff=3600)

        # Build up backoff
        rl.record_error()
        rl.record_error()
        rl.record_error()

        # Success should reset
        rl.record_success()

        # Should be back to normal range
        delay = rl.get_current_delay()
        assert 10 <= delay <= 60
