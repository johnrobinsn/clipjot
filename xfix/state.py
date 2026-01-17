"""State management for cursor, retries, and backoff."""

import json
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class RetryInfo:
    """Retry information for a single URL."""

    attempts: int
    last_attempt: str  # ISO format timestamp
    error_type: str  # network, rate_limit, parse, ollama
    bookmark_id: int


@dataclass
class FailedBookmark:
    """Permanently failed bookmark."""

    url: str
    bookmark_id: int
    attempts: int
    last_error: str
    failed_at: str  # ISO format timestamp


@dataclass
class BackoffState:
    """Global Fibonacci backoff state."""

    current_delay: float
    fibonacci_index: int


@dataclass
class State:
    """Complete application state."""

    cursor: str | None = None
    last_updated: str | None = None
    retries: dict[str, RetryInfo] = field(default_factory=dict)
    failed: list[FailedBookmark] = field(default_factory=list)
    backoff: BackoffState = field(default_factory=lambda: BackoffState(0, 0))


# Fibonacci sequence for backoff multipliers
FIBONACCI = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144]


class StateManager:
    """Manages persistent state with atomic writes."""

    def __init__(self, state_file: Path, base_delay: float, max_backoff: float):
        """
        Initialize state manager.

        Args:
            state_file: Path to state JSON file.
            base_delay: Base delay for backoff calculation (midpoint of min/max).
            max_backoff: Maximum backoff delay in seconds.
        """
        self.state_file = state_file
        self.base_delay = base_delay
        self.max_backoff = max_backoff
        self.state = State()

    def load(self) -> None:
        """Load state from file if it exists."""
        if not self.state_file.exists():
            return

        try:
            with open(self.state_file) as f:
                data = json.load(f)

            self.state.cursor = data.get("cursor")
            self.state.last_updated = data.get("last_updated")

            # Load retries
            for url, info in data.get("retries", {}).items():
                self.state.retries[url] = RetryInfo(
                    attempts=info["attempts"],
                    last_attempt=info["last_attempt"],
                    error_type=info["error_type"],
                    bookmark_id=info["bookmark_id"],
                )

            # Load failed bookmarks
            for item in data.get("failed", []):
                self.state.failed.append(
                    FailedBookmark(
                        url=item["url"],
                        bookmark_id=item["bookmark_id"],
                        attempts=item["attempts"],
                        last_error=item["last_error"],
                        failed_at=item["failed_at"],
                    )
                )

            # Load backoff state
            if "backoff" in data:
                self.state.backoff = BackoffState(
                    current_delay=data["backoff"]["current_delay"],
                    fibonacci_index=data["backoff"]["fibonacci_index"],
                )

        except (json.JSONDecodeError, KeyError) as e:
            # Corrupted state file - start fresh but log warning
            raise ValueError(f"Corrupted state file: {e}") from e

    def save(self) -> None:
        """Save state to file atomically."""
        self.state.last_updated = datetime.now(timezone.utc).isoformat()

        data = {
            "cursor": self.state.cursor,
            "last_updated": self.state.last_updated,
            "retries": {
                url: {
                    "attempts": info.attempts,
                    "last_attempt": info.last_attempt,
                    "error_type": info.error_type,
                    "bookmark_id": info.bookmark_id,
                }
                for url, info in self.state.retries.items()
            },
            "failed": [
                {
                    "url": fb.url,
                    "bookmark_id": fb.bookmark_id,
                    "attempts": fb.attempts,
                    "last_error": fb.last_error,
                    "failed_at": fb.failed_at,
                }
                for fb in self.state.failed
            ],
            "backoff": {
                "current_delay": self.state.backoff.current_delay,
                "fibonacci_index": self.state.backoff.fibonacci_index,
            },
        }

        # Atomic write: write to temp file, then rename
        dir_path = self.state_file.parent if self.state_file.parent != Path() else Path(".")
        with tempfile.NamedTemporaryFile(
            mode="w", dir=dir_path, suffix=".tmp", delete=False
        ) as f:
            json.dump(data, f, indent=2)
            temp_path = Path(f.name)

        temp_path.rename(self.state_file)

    def get_cursor(self) -> str | None:
        """Get current sync cursor."""
        return self.state.cursor

    def set_cursor(self, cursor: str) -> None:
        """Update sync cursor and save immediately."""
        self.state.cursor = cursor
        self.save()

    def clear_cursor(self) -> None:
        """Clear cursor for --from-start."""
        self.state.cursor = None

    def record_error(self, url: str, bookmark_id: int, error_type: str, max_attempts: int = 3) -> bool:
        """
        Record a fetch/enrichment error.

        Args:
            url: The URL that failed.
            bookmark_id: The bookmark ID.
            error_type: Type of error (network, rate_limit, parse, ollama, not_found).
            max_attempts: Maximum retry attempts before permanent failure.

        Returns:
            True if should retry, False if permanently failed.
        """
        now = datetime.now(timezone.utc).isoformat()

        # not_found errors fail immediately
        if error_type == "not_found":
            self._mark_failed(url, bookmark_id, 1, error_type, now)
            return False

        if url in self.state.retries:
            info = self.state.retries[url]
            info.attempts += 1
            info.last_attempt = now
            info.error_type = error_type
        else:
            self.state.retries[url] = RetryInfo(
                attempts=1,
                last_attempt=now,
                error_type=error_type,
                bookmark_id=bookmark_id,
            )

        # Check if max attempts reached
        if self.state.retries[url].attempts >= max_attempts:
            self._mark_failed(url, bookmark_id, max_attempts, error_type, now)
            return False

        return True

    def _mark_failed(self, url: str, bookmark_id: int, attempts: int, error_type: str, timestamp: str) -> None:
        """Move URL from retries to failed list."""
        if url in self.state.retries:
            del self.state.retries[url]

        self.state.failed.append(
            FailedBookmark(
                url=url,
                bookmark_id=bookmark_id,
                attempts=attempts,
                last_error=error_type,
                failed_at=timestamp,
            )
        )

    def record_success(self, url: str) -> None:
        """Record successful fetch - remove from retries, reset backoff."""
        if url in self.state.retries:
            del self.state.retries[url]

        # Reset backoff on success
        self.state.backoff = BackoffState(0, 0)

    def is_failed(self, url: str) -> bool:
        """Check if URL has permanently failed."""
        return any(fb.url == url for fb in self.state.failed)

    def get_retry_count(self, url: str) -> int:
        """Get current retry count for URL."""
        if url in self.state.retries:
            return self.state.retries[url].attempts
        return 0

    def increment_backoff(self) -> float:
        """
        Increment global backoff and return new delay.

        Uses Fibonacci sequence: base × fib[index].
        """
        idx = self.state.backoff.fibonacci_index
        if idx < len(FIBONACCI):
            multiplier = FIBONACCI[idx]
        else:
            multiplier = FIBONACCI[-1]

        delay = min(self.base_delay * multiplier, self.max_backoff)
        self.state.backoff.current_delay = delay
        self.state.backoff.fibonacci_index = idx + 1

        return delay

    def get_current_backoff(self) -> float:
        """Get current backoff delay (0 if not in backoff)."""
        return self.state.backoff.current_delay

    def reset_backoff(self) -> None:
        """Reset backoff to initial state."""
        self.state.backoff = BackoffState(0, 0)
