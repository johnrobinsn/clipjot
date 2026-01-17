# XFix Specification

A standalone Python script that automatically enriches X.com (Twitter) bookmarks in LinkJot/ClipJot with AI-generated titles and comments using Ollama.

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Configuration](#configuration)
4. [Bookmark Discovery](#bookmark-discovery)
5. [X.com Content Fetching](#xcom-content-fetching)
6. [AI Enrichment](#ai-enrichment)
7. [State Management](#state-management)
8. [Error Handling & Retry Logic](#error-handling--retry-logic)
9. [Logging](#logging)
10. [Command-Line Interface](#command-line-interface)
11. [Testing Strategy](#testing-strategy)

---

## Overview

XFix monitors a ClipJot instance for new bookmarks from X.com (Twitter), fetches the tweet content, and uses a local Ollama instance to generate:

- **Title**: A brief one-sentence description of the tweet
- **Comment**: A 3-5 sentence summary of the content

The script only processes bookmarks where the title OR comment is empty, preserving any user-provided metadata.

### Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Architecture | Standalone Python script | Simple deployment, will move to own repo |
| Discovery | Long-polling sync API | Real-time notification of new bookmarks |
| Content fetch | Direct HTTP requests | Simple first approach, with retry on failure |
| AI backend | Local Ollama | Privacy, no API costs, configurable model |
| State persistence | JSON file | Simple, human-readable, easy to debug |
| User scope | Single user | One API token per instance |

---

## Architecture

### Directory Structure

```
xfix/
├── xfix.py              # Main script entry point
├── fetcher.py           # X.com content fetching logic
├── enricher.py          # Ollama integration for AI generation
├── api_client.py        # ClipJot API client
├── state.py             # State management (cursor, retries)
├── config.py            # Configuration loading from .env
├── .env                 # Configuration (not committed)
├── .env.example         # Example configuration
├── state.json           # Persistent state (cursor + retry tracking)
├── tests/
│   ├── conftest.py
│   ├── test_fetcher.py
│   ├── test_enricher.py
│   ├── test_api_client.py
│   └── test_state.py
├── requirements.txt
├── SPEC.md
└── README.md
```

### Dependencies

- Python 3.12+ (via conda environment `ClipJot`)
- `httpx` - Async HTTP client for API calls
- `python-dotenv` - Configuration from .env files
- `ollama` - Official Ollama Python client
- `pytest` - Testing framework
- `pytest-asyncio` - Async test support

---

## Configuration

Configuration via `.env` file using python-dotenv:

```bash
# ClipJot API
CLIPJOT_API_URL=https://clipjot.example.com
CLIPJOT_API_TOKEN=your-api-token-here

# Ollama
OLLAMA_MODEL=qwen3                    # Model name (default: qwen3)
OLLAMA_HOST=http://localhost:11434    # Ollama API endpoint

# X.com Fetch Delays
XCOM_MIN_DELAY=10                     # Minimum delay between X.com requests (seconds)
XCOM_MAX_DELAY=60                     # Maximum delay between X.com requests (seconds)
XCOM_MAX_BACKOFF=3600                 # Maximum backoff delay (1 hour, in seconds)

# State
STATE_FILE=state.json                 # Path to state file

# Logging
LOG_LEVEL=INFO                        # DEBUG, INFO, WARNING, ERROR
LOG_VERBOSE=true                      # Show full generated content (true/false)
```

### Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `CLIPJOT_API_URL` | Yes | - | Base URL of ClipJot instance |
| `CLIPJOT_API_TOKEN` | Yes | - | API token with write scope |
| `OLLAMA_MODEL` | No | `qwen3` | Ollama model for summarization |
| `OLLAMA_HOST` | No | `http://localhost:11434` | Ollama API endpoint |
| `XCOM_MIN_DELAY` | No | `10` | Min seconds between X.com fetches |
| `XCOM_MAX_DELAY` | No | `60` | Max seconds between X.com fetches |
| `XCOM_MAX_BACKOFF` | No | `3600` | Max backoff delay on errors (seconds) |
| `STATE_FILE` | No | `state.json` | Path to persistent state file |
| `LOG_LEVEL` | No | `INFO` | Logging verbosity |
| `LOG_VERBOSE` | No | `true` | Show generated titles/comments |

---

## Bookmark Discovery

### Long-Polling Sync API

The script uses ClipJot's `/api/v1/bookmarks/sync` endpoint with long polling to receive real-time notifications of new bookmarks.

**Flow:**

1. Load saved cursor from state file (or start from beginning if none/`--from-start`)
2. Call sync API with cursor, using long-poll timeout
3. Filter response for X.com URLs
4. Process matching bookmarks that need enrichment
5. Save updated cursor to state file
6. Repeat from step 2

### X.com URL Detection

Match all common X/Twitter URL patterns:

```python
X_URL_PATTERNS = [
    r'https?://(www\.)?x\.com/',
    r'https?://(www\.)?twitter\.com/',
    r'https?://mobile\.twitter\.com/',
    r'https?://m\.twitter\.com/',
]
```

### Processing Criteria

A bookmark is eligible for enrichment if:

1. URL matches an X.com pattern, AND
2. Title is empty/null OR comment is empty/null

If both title and comment are already populated, skip the bookmark.

---

## X.com Content Fetching

### Direct HTTP Fetch

Attempt to fetch tweet content via direct HTTP request:

```python
async def fetch_tweet(url: str) -> TweetContent | None:
    """
    Fetch tweet content from X.com URL.

    Returns TweetContent with text, author, etc. on success.
    Returns None on failure (will be retried).
    """
```

### Rate Limiting & Delays

**Normal operation:**
- Random delay between `XCOM_MIN_DELAY` and `XCOM_MAX_DELAY` seconds before each X.com request

**On error (Fibonacci backoff):**
- Backoff is **global** (affects all X.com requests, not per-URL)
- Sequence: base delay → base×1 → base×2 → base×3 → base×5 → base×8 → ...
- Maximum backoff: `XCOM_MAX_BACKOFF` (default 1 hour)
- On success: reset to normal random delay

**Example with defaults (min=10, max=60):**
1. Normal: random 10-60s delay
2. First error: ~35s (midpoint)
3. Second error: ~70s
4. Third error: ~105s
5. ...continues with Fibonacci multipliers...
6. Caps at 3600s (1 hour)
7. On success: back to random 10-60s

---

## AI Enrichment

### Ollama Integration

**Startup check:**
- Verify Ollama is running and model is available
- Exit with error if Ollama is not reachable

**Prompt design:**

```
Given the following tweet content, generate:
1. A brief one-sentence title (max 100 characters)
2. A 3-5 sentence summary

Tweet by @{author}:
{tweet_text}

Respond in this exact format:
TITLE: <your title here>
SUMMARY: <your summary here>
```

### Output Parsing

Parse Ollama response to extract:
- **Title**: Text after "TITLE:" (trimmed, max 100 chars)
- **Comment**: Text after "SUMMARY:" (trimmed)

If parsing fails, treat as enrichment error (differentiated from fetch error).

---

## State Management

### State File Format

Single JSON file (`state.json`) containing:

```json
{
  "cursor": "eyJpZCI6MTIzNDV9",
  "last_updated": "2024-01-15T10:30:00Z",
  "retries": {
    "https://x.com/user/status/123": {
      "attempts": 2,
      "last_attempt": "2024-01-15T10:25:00Z",
      "error_type": "network"
    }
  },
  "failed": [
    {
      "url": "https://x.com/user/status/456",
      "bookmark_id": 789,
      "attempts": 3,
      "last_error": "network",
      "failed_at": "2024-01-15T10:20:00Z"
    }
  ],
  "backoff": {
    "current_delay": 35,
    "fibonacci_index": 0
  }
}
```

### State Operations

- **Load on startup**: Read cursor and retry state
- **Save after each sync**: Update cursor immediately after successful sync API call
- **Save on shutdown**: Persist current state on graceful shutdown
- **Atomic writes**: Write to temp file, then rename to prevent corruption

---

## Error Handling & Retry Logic

### Error Types (Differentiated)

| Error Type | Description | Retriable | Max Attempts |
|------------|-------------|-----------|--------------|
| `network` | Connection timeout, DNS failure, HTTP 5xx | Yes | 3 |
| `rate_limit` | HTTP 429 from X.com | Yes | 3 |
| `not_found` | HTTP 404, tweet deleted | No | 1 |
| `parse` | Cannot extract content from response | Yes | 3 |
| `ollama` | Ollama API error or parse failure | Yes | 3 |

### Retry Behavior

- **Network/rate_limit errors**: Increment global backoff, add to retry queue
- **Not found errors**: Mark as permanently failed immediately
- **Parse errors**: Retry up to 3 times (page structure may vary)
- **Ollama errors**: Retry up to 3 times (model may give different output)

### Permanent Failure

After 3 failed attempts (for retriable errors):
- Move from `retries` to `failed` list in state
- Log the failure with details
- Do not attempt again in future runs

---

## Logging

### Log Levels

```
DEBUG   - Detailed trace (API requests/responses, parsing steps)
INFO    - Normal operation (processing bookmark X, enriched Y)
WARNING - Recoverable issues (fetch failed, will retry)
ERROR   - Failures (max retries exceeded, Ollama down)
```

### Log Format

```
2024-01-15 10:30:00 INFO  Processing bookmark 12345: https://x.com/user/status/123
2024-01-15 10:30:02 INFO  Fetched tweet content (234 chars)
2024-01-15 10:30:05 INFO  Generated title: "Author discusses new AI research findings"
2024-01-15 10:30:05 INFO  Generated comment: "The tweet covers recent developments in..."
2024-01-15 10:30:06 INFO  Updated bookmark 12345 successfully
```

### Verbose Mode

When `LOG_VERBOSE=true` (default), log full generated content:

```
2024-01-15 10:30:05 INFO  Enriched bookmark 12345
  URL: https://x.com/user/status/123
  Title: Author discusses new AI research findings
  Comment: The tweet covers recent developments in large language models.
           The author highlights three key breakthroughs from the past month.
           They also mention potential applications in healthcare and education.
```

When `LOG_VERBOSE=false`:

```
2024-01-15 10:30:05 INFO  Enriched: https://x.com/user/status/123
```

---

## Command-Line Interface

### Usage

```bash
python xfix.py [OPTIONS]
```

### Options

| Option | Description |
|--------|-------------|
| `--from-start` | Ignore saved cursor, process all bookmarks from beginning |
| `--dry-run` | Fetch and generate content but don't update ClipJot API |
| `--verbose` / `-v` | Override LOG_VERBOSE to true |
| `--quiet` / `-q` | Override LOG_VERBOSE to false |
| `--help` / `-h` | Show help message |

### Examples

```bash
# Normal operation (resume from saved cursor)
python xfix.py

# Start fresh, ignore previous progress
python xfix.py --from-start

# Test without making changes
python xfix.py --dry-run

# Quiet mode for cron/background
python xfix.py -q
```

### Graceful Shutdown

On SIGINT (Ctrl+C) or SIGTERM:

1. Stop accepting new bookmarks from sync API
2. Complete processing of current bookmark (if any)
3. Save state to JSON file
4. Exit cleanly

---

## Testing Strategy

### Framework

- **pytest** with pytest-asyncio for async tests
- Mocked external dependencies (ClipJot API, Ollama, X.com)

### Test Coverage

#### Unit Tests

**`test_fetcher.py`**
- URL pattern matching (all X/Twitter variants)
- Content extraction from mocked HTML responses
- Error handling for various HTTP status codes
- Delay calculation with Fibonacci backoff

**`test_enricher.py`**
- Ollama prompt construction
- Response parsing (title/comment extraction)
- Handling of malformed Ollama responses
- Startup connectivity check

**`test_api_client.py`**
- Sync API long-polling behavior
- Bookmark filtering (X.com URLs only)
- Edit API request construction
- Authentication header handling

**`test_state.py`**
- State file loading/saving
- Cursor persistence
- Retry queue management
- Failed bookmark tracking
- Atomic file writes

### Running Tests

```bash
cd xfix
conda activate ClipJot
pytest tests/ -v
```

### Test Fixtures

```python
@pytest.fixture
def mock_clipjot_api():
    """Mock ClipJot API responses."""
    ...

@pytest.fixture
def mock_ollama():
    """Mock Ollama API with predefined responses."""
    ...

@pytest.fixture
def mock_xcom_response():
    """Mock X.com page HTML for content extraction."""
    ...

@pytest.fixture
def state_file(tmp_path):
    """Temporary state file for testing."""
    ...
```

---

## Future Considerations

These features are explicitly **out of scope** for initial implementation:

- **Thread handling**: Fetching and summarizing entire X.com threads
- **Browser automation**: Using Playwright/Selenium for JavaScript-rendered content
- **External proxies**: Using Nitter, FxTwitter, or similar services
- **Multi-user support**: Processing bookmarks for multiple ClipJot users
- **Coverage analysis**: Adding pytest-cov thresholds
- **Media extraction**: Handling images, videos, or polls in tweets
