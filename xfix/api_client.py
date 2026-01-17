"""ClipJot API client for sync and bookmark operations."""

import re
from dataclasses import dataclass

import httpx

# X.com URL patterns to match
X_URL_PATTERNS = [
    re.compile(r"https?://(www\.)?x\.com/"),
    re.compile(r"https?://(www\.)?twitter\.com/"),
    re.compile(r"https?://mobile\.twitter\.com/"),
    re.compile(r"https?://m\.twitter\.com/"),
]


@dataclass
class Bookmark:
    """Bookmark data from API."""

    id: int
    url: str
    title: str | None
    comment: str | None
    tags: list[dict]
    client_name: str | None
    created_at: str
    updated_at: str | None = None


@dataclass
class SyncResponse:
    """Response from sync API."""

    bookmarks: list[Bookmark]
    cursor: str | None
    has_more: bool
    waited: bool


def is_x_url(url: str) -> bool:
    """Check if URL is from X.com/Twitter."""
    return any(pattern.match(url) for pattern in X_URL_PATTERNS)


def needs_enrichment(bookmark: Bookmark) -> bool:
    """Check if bookmark needs title or comment enrichment."""
    return not bookmark.title or not bookmark.comment


class ClipJotClient:
    """Async client for ClipJot API."""

    def __init__(self, base_url: str, api_token: str, timeout: float = 120.0):
        """
        Initialize the client.

        Args:
            base_url: ClipJot API base URL (e.g., https://clipjot.example.com)
            api_token: API token with read+write scope
            timeout: Request timeout in seconds (long for sync polling)
        """
        self.base_url = base_url.rstrip("/")
        self.api_token = api_token
        self.timeout = timeout

    def _headers(self) -> dict[str, str]:
        """Build request headers with auth."""
        return {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }

    async def sync(
        self,
        cursor: str | None = None,
        limit: int = 50,
        wait: bool = True,
    ) -> SyncResponse:
        """
        Sync bookmarks using long-polling.

        Args:
            cursor: Bookmark ID to start after (None for beginning)
            limit: Max bookmarks to return (1-100)
            wait: Whether to long-poll for new bookmarks

        Returns:
            SyncResponse with bookmarks and new cursor
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/v1/bookmarks/sync",
                headers=self._headers(),
                json={
                    "cursor": cursor,
                    "limit": limit,
                    "wait": wait,
                },
            )
            response.raise_for_status()
            data = response.json()

        bookmarks = [
            Bookmark(
                id=b["id"],
                url=b["url"],
                title=b.get("title"),
                comment=b.get("comment"),
                tags=b.get("tags", []),
                client_name=b.get("client_name"),
                created_at=b["created_at"],
                updated_at=b.get("updated_at"),
            )
            for b in data.get("bookmarks", [])
        ]

        return SyncResponse(
            bookmarks=bookmarks,
            cursor=data.get("cursor"),
            has_more=data.get("has_more", False),
            waited=data.get("waited", False),
        )

    async def edit_bookmark(
        self,
        bookmark_id: int,
        title: str | None = None,
        comment: str | None = None,
    ) -> Bookmark:
        """
        Update a bookmark's title and/or comment.

        Args:
            bookmark_id: ID of bookmark to update
            title: New title (None to leave unchanged)
            comment: New comment (None to leave unchanged)

        Returns:
            Updated Bookmark
        """
        payload: dict = {"id": bookmark_id}
        if title is not None:
            payload["title"] = title
        if comment is not None:
            payload["comment"] = comment

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/api/v1/bookmarks/edit",
                headers=self._headers(),
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        return Bookmark(
            id=data["id"],
            url=data["url"],
            title=data.get("title"),
            comment=data.get("comment"),
            tags=data.get("tags", []),
            client_name=data.get("client_name"),
            created_at=data["created_at"],
            updated_at=data.get("updated_at"),
        )

    async def get_x_bookmarks_needing_enrichment(
        self,
        cursor: str | None = None,
        limit: int = 50,
        wait: bool = True,
    ) -> tuple[list[Bookmark], str | None, bool]:
        """
        Sync and filter for X.com bookmarks needing enrichment.

        Args:
            cursor: Bookmark ID to start after
            limit: Max bookmarks to fetch
            wait: Whether to long-poll

        Returns:
            Tuple of (matching bookmarks, new cursor, has_more)
        """
        response = await self.sync(cursor=cursor, limit=limit, wait=wait)

        matching = [
            b for b in response.bookmarks
            if is_x_url(b.url) and needs_enrichment(b)
        ]

        return matching, response.cursor, response.has_more
