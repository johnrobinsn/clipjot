"""X.com content fetching with rate limiting and retry logic.

This module fetches tweet content using multiple strategies in order of reliability:

1. **fxtwitter API** (Primary)
   - Endpoint: https://api.fxtwitter.com/{username}/status/{tweet_id}
   - Returns rich JSON with full tweet text, author info, and engagement metrics
   - No authentication required
   - Third-party service that scrapes Twitter/X

2. **Twitter oEmbed API** (Fallback)
   - Endpoint: https://publish.twitter.com/oembed?url={tweet_url}
   - Official Twitter API, no auth required
   - Returns HTML snippet that we parse to extract text
   - Less metadata than fxtwitter but more stable

3. **Direct HTML scraping** (Last resort)
   - Fetches X.com page directly and extracts OpenGraph meta tags
   - Often fails because X.com uses JavaScript rendering
   - Kept as fallback in case other APIs are unavailable
"""

import asyncio
import html
import random
import re
from dataclasses import dataclass, field
from enum import Enum

import httpx


class ErrorType(Enum):
    """Types of fetch errors for differentiated handling."""

    NETWORK = "network"  # Connection timeout, DNS failure, HTTP 5xx
    RATE_LIMIT = "rate_limit"  # HTTP 429
    NOT_FOUND = "not_found"  # HTTP 404, tweet deleted
    PARSE = "parse"  # Cannot extract content from response


@dataclass
class TweetContent:
    """Extracted tweet content."""

    author: str
    text: str
    url: str
    author_name: str | None = None
    likes: int | None = None
    retweets: int | None = None
    replies: int | None = None
    views: int | None = None


@dataclass
class FetchResult:
    """Result of a fetch attempt."""

    success: bool
    content: TweetContent | None = None
    error_type: ErrorType | None = None
    error_message: str | None = None


# Pattern to extract tweet ID from URL
TWEET_ID_PATTERN = re.compile(r"/status/(\d+)")

# Pattern to extract author from URL
AUTHOR_PATTERN = re.compile(r"(?:x\.com|twitter\.com)/([^/]+)/status")

# Patterns to extract tweet text from HTML meta tags
META_DESCRIPTION_PATTERN = re.compile(
    r'<meta\s+(?:property="og:description"|name="description")\s+content="([^"]*)"',
    re.IGNORECASE,
)
META_TITLE_PATTERN = re.compile(
    r'<meta\s+property="og:title"\s+content="([^"]*)"',
    re.IGNORECASE,
)

# User agent to mimic browser
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


def extract_tweet_id(url: str) -> str | None:
    """Extract tweet ID from X.com URL."""
    match = TWEET_ID_PATTERN.search(url)
    return match.group(1) if match else None


def extract_author(url: str) -> str | None:
    """Extract author username from X.com URL."""
    match = AUTHOR_PATTERN.search(url)
    return match.group(1) if match else None


async def fetch_via_fxtwitter(url: str, timeout: float = 30.0) -> FetchResult:
    """
    Fetch tweet content via fxtwitter API.

    fxtwitter is a third-party service that provides rich JSON data for tweets.
    API endpoint: https://api.fxtwitter.com/{username}/status/{tweet_id}

    Args:
        url: X.com tweet URL
        timeout: Request timeout in seconds

    Returns:
        FetchResult with tweet content or error info
    """
    username = extract_author(url)
    tweet_id = extract_tweet_id(url)

    if not username or not tweet_id:
        return FetchResult(
            success=False,
            error_type=ErrorType.PARSE,
            error_message="Could not extract username/tweet_id from URL",
        )

    api_url = f"https://api.fxtwitter.com/{username}/status/{tweet_id}"

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(
                api_url,
                headers={"User-Agent": USER_AGENT},
            )

            if response.status_code == 404:
                return FetchResult(
                    success=False,
                    error_type=ErrorType.NOT_FOUND,
                    error_message="Tweet not found via fxtwitter (404)",
                )

            if response.status_code in (429, 403):
                # 403 can also indicate rate limiting or blocked
                return FetchResult(
                    success=False,
                    error_type=ErrorType.RATE_LIMIT,
                    error_message=f"Rate limited by fxtwitter ({response.status_code})",
                )

            if response.status_code != 200:
                return FetchResult(
                    success=False,
                    error_type=ErrorType.NETWORK,
                    error_message=f"fxtwitter returned status {response.status_code}",
                )

            data = response.json()

            # Check for error response
            if data.get("code") != 200:
                return FetchResult(
                    success=False,
                    error_type=ErrorType.NOT_FOUND,
                    error_message=data.get("message", "Unknown fxtwitter error"),
                )

            tweet = data.get("tweet", {})
            text = tweet.get("text", "")
            author_info = tweet.get("author", {})

            if not text:
                return FetchResult(
                    success=False,
                    error_type=ErrorType.PARSE,
                    error_message="No text in fxtwitter response",
                )

            return FetchResult(
                success=True,
                content=TweetContent(
                    author=author_info.get("screen_name", username),
                    author_name=author_info.get("name"),
                    text=text,
                    url=url,
                    likes=tweet.get("likes"),
                    retweets=tweet.get("retweets"),
                    replies=tweet.get("replies"),
                    views=tweet.get("views"),
                ),
            )

    except httpx.TimeoutException:
        return FetchResult(
            success=False,
            error_type=ErrorType.NETWORK,
            error_message="fxtwitter request timed out",
        )
    except httpx.HTTPError as e:
        return FetchResult(
            success=False,
            error_type=ErrorType.NETWORK,
            error_message=f"fxtwitter HTTP error: {e}",
        )
    except Exception as e:
        return FetchResult(
            success=False,
            error_type=ErrorType.PARSE,
            error_message=f"fxtwitter parse error: {e}",
        )


# Pattern to extract tweet text from oEmbed HTML response
OEMBED_TEXT_PATTERN = re.compile(r"<p[^>]*>(.*?)</p>", re.DOTALL)


async def fetch_via_oembed(url: str, timeout: float = 30.0) -> FetchResult:
    """
    Fetch tweet content via Twitter's oEmbed API.

    oEmbed is Twitter's official embedding API that returns HTML snippets.
    API endpoint: https://publish.twitter.com/oembed?url={tweet_url}

    Args:
        url: X.com tweet URL
        timeout: Request timeout in seconds

    Returns:
        FetchResult with tweet content or error info
    """
    # Normalize URL to twitter.com format (oEmbed prefers this)
    normalized_url = url.replace("x.com", "twitter.com")
    api_url = f"https://publish.twitter.com/oembed?url={normalized_url}"

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(api_url)

            if response.status_code == 404:
                return FetchResult(
                    success=False,
                    error_type=ErrorType.NOT_FOUND,
                    error_message="Tweet not found via oEmbed (404)",
                )

            if response.status_code == 429:
                return FetchResult(
                    success=False,
                    error_type=ErrorType.RATE_LIMIT,
                    error_message="Rate limited by oEmbed (429)",
                )

            if response.status_code != 200:
                return FetchResult(
                    success=False,
                    error_type=ErrorType.NETWORK,
                    error_message=f"oEmbed returned status {response.status_code}",
                )

            data = response.json()

            # Extract text from HTML
            html_content = data.get("html", "")
            match = OEMBED_TEXT_PATTERN.search(html_content)

            if not match:
                return FetchResult(
                    success=False,
                    error_type=ErrorType.PARSE,
                    error_message="Could not extract text from oEmbed HTML",
                )

            # Clean up the extracted text
            text = match.group(1)
            # Remove HTML tags (like <a> links)
            text = re.sub(r"<[^>]+>", "", text)
            # Decode HTML entities
            text = html.unescape(text)
            text = text.strip()

            if not text:
                return FetchResult(
                    success=False,
                    error_type=ErrorType.PARSE,
                    error_message="Empty text after parsing oEmbed HTML",
                )

            author = extract_author(url) or "unknown"
            author_name = data.get("author_name")

            return FetchResult(
                success=True,
                content=TweetContent(
                    author=author,
                    author_name=author_name,
                    text=text,
                    url=url,
                ),
            )

    except httpx.TimeoutException:
        return FetchResult(
            success=False,
            error_type=ErrorType.NETWORK,
            error_message="oEmbed request timed out",
        )
    except httpx.HTTPError as e:
        return FetchResult(
            success=False,
            error_type=ErrorType.NETWORK,
            error_message=f"oEmbed HTTP error: {e}",
        )
    except Exception as e:
        return FetchResult(
            success=False,
            error_type=ErrorType.PARSE,
            error_message=f"oEmbed parse error: {e}",
        )


def parse_tweet_from_html(html: str, url: str) -> TweetContent | None:
    """
    Parse tweet content from HTML response.

    Attempts to extract content from OpenGraph meta tags.
    """
    author = extract_author(url) or "unknown"

    # Try og:description first (usually contains tweet text)
    desc_match = META_DESCRIPTION_PATTERN.search(html)
    if desc_match:
        text = desc_match.group(1)
        # Unescape HTML entities
        text = (
            text.replace("&quot;", '"')
            .replace("&amp;", "&")
            .replace("&lt;", "<")
            .replace("&gt;", ">")
            .replace("&#39;", "'")
        )
        if text and len(text) > 10:  # Sanity check
            return TweetContent(author=author, text=text, url=url)

    # Fallback to og:title
    title_match = META_TITLE_PATTERN.search(html)
    if title_match:
        text = title_match.group(1)
        text = (
            text.replace("&quot;", '"')
            .replace("&amp;", "&")
            .replace("&lt;", "<")
            .replace("&gt;", ">")
            .replace("&#39;", "'")
        )
        # Title often has format "Author on X: tweet text"
        if " on X: " in text:
            text = text.split(" on X: ", 1)[1]
        elif " on Twitter: " in text:
            text = text.split(" on Twitter: ", 1)[1]
        if text and len(text) > 10:
            return TweetContent(author=author, text=text, url=url)

    return None


async def fetch_via_html(url: str, timeout: float = 30.0) -> FetchResult:
    """
    Fetch tweet content by scraping X.com directly.

    This is a last resort fallback that attempts to extract content from
    OpenGraph meta tags in the HTML. Often fails because X.com uses
    JavaScript rendering.

    Args:
        url: X.com tweet URL
        timeout: Request timeout in seconds

    Returns:
        FetchResult with tweet content or error info
    """
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }

    try:
        async with httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=True,
        ) as client:
            response = await client.get(url, headers=headers)

            if response.status_code == 404:
                return FetchResult(
                    success=False,
                    error_type=ErrorType.NOT_FOUND,
                    error_message="Tweet not found (404)",
                )

            if response.status_code == 429:
                return FetchResult(
                    success=False,
                    error_type=ErrorType.RATE_LIMIT,
                    error_message="Rate limited by X.com (429)",
                )

            if response.status_code >= 500:
                return FetchResult(
                    success=False,
                    error_type=ErrorType.NETWORK,
                    error_message=f"Server error ({response.status_code})",
                )

            if response.status_code != 200:
                return FetchResult(
                    success=False,
                    error_type=ErrorType.NETWORK,
                    error_message=f"Unexpected status code: {response.status_code}",
                )

            # Parse content
            html_text = response.text
            content = parse_tweet_from_html(html_text, url)

            if content:
                return FetchResult(success=True, content=content)
            else:
                return FetchResult(
                    success=False,
                    error_type=ErrorType.PARSE,
                    error_message="Could not extract tweet content from HTML",
                )

    except httpx.TimeoutException:
        return FetchResult(
            success=False,
            error_type=ErrorType.NETWORK,
            error_message="HTML scrape request timed out",
        )
    except httpx.ConnectError as e:
        return FetchResult(
            success=False,
            error_type=ErrorType.NETWORK,
            error_message=f"HTML scrape connection error: {e}",
        )
    except httpx.HTTPError as e:
        return FetchResult(
            success=False,
            error_type=ErrorType.NETWORK,
            error_message=f"HTML scrape HTTP error: {e}",
        )


async def fetch_tweet(url: str, timeout: float = 30.0) -> FetchResult:
    """
    Fetch tweet content from X.com URL using multiple strategies.

    Tries these methods in order until one succeeds:
    1. fxtwitter API - third-party service with rich JSON data
    2. Twitter oEmbed API - official embedding API
    3. Direct HTML scraping - last resort, often fails

    Args:
        url: X.com tweet URL
        timeout: Request timeout in seconds

    Returns:
        FetchResult indicating success/failure with content or error info
    """
    # Strategy 1: fxtwitter API (best data)
    result = await fetch_via_fxtwitter(url, timeout)
    if result.success:
        return result

    # If tweet not found, don't try other methods
    if result.error_type == ErrorType.NOT_FOUND:
        return result

    # Strategy 2: Twitter oEmbed API (official, more stable)
    result = await fetch_via_oembed(url, timeout)
    if result.success:
        return result

    # If tweet not found, don't try other methods
    if result.error_type == ErrorType.NOT_FOUND:
        return result

    # Strategy 3: Direct HTML scraping (last resort)
    return await fetch_via_html(url, timeout)


class RateLimiter:
    """Rate limiter with Fibonacci backoff for X.com requests."""

    def __init__(self, min_delay: float, max_delay: float, max_backoff: float):
        """
        Initialize rate limiter.

        Args:
            min_delay: Minimum delay between requests (seconds)
            max_delay: Maximum normal delay between requests (seconds)
            max_backoff: Maximum backoff delay on errors (seconds)
        """
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.max_backoff = max_backoff
        self._backoff_delay: float = 0
        self._fibonacci_index: int = 0

    @property
    def base_delay(self) -> float:
        """Get base delay (midpoint of min/max)."""
        return (self.min_delay + self.max_delay) / 2

    def get_normal_delay(self) -> float:
        """Get random delay for normal operation."""
        return random.uniform(self.min_delay, self.max_delay)

    def get_current_delay(self) -> float:
        """Get current delay (backoff or normal)."""
        if self._backoff_delay > 0:
            return self._backoff_delay
        return self.get_normal_delay()

    def record_success(self) -> None:
        """Reset backoff after successful request."""
        self._backoff_delay = 0
        self._fibonacci_index = 0

    def record_error(self) -> float:
        """
        Increment backoff after error.

        Returns:
            New backoff delay
        """
        fibonacci = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144]
        idx = min(self._fibonacci_index, len(fibonacci) - 1)
        multiplier = fibonacci[idx]

        self._backoff_delay = min(self.base_delay * multiplier, self.max_backoff)
        self._fibonacci_index += 1

        return self._backoff_delay

    async def wait(self) -> None:
        """Wait for the appropriate delay before next request."""
        delay = self.get_current_delay()
        if delay > 0:
            await asyncio.sleep(delay)
