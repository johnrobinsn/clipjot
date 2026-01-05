# LinkJot Specification

A bookmark management system with multiple clients for capturing bookmarks and a backend for storing, searching, and managing them.

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Backend](#backend)
   - [CLI Reference](#cli-reference)
4. [Clients](#clients)
5. [Data Model](#data-model)
6. [API Specification](#api-specification)
7. [Authentication & Authorization](#authentication--authorization)
8. [User Interface](#user-interface)
   - [Admin UI](#admin-ui)
9. [Testing Strategy](#testing-strategy)
10. [Deployment](#deployment)
11. [Hosted Instance](#hosted-instance)

---

## Overview

LinkJot is a self-hostable bookmark management system that allows users to save, organize, and search bookmarks from multiple platforms. The system consists of:

- **Backend**: FastHTML-based web application with API, database, and admin UI
- **Chrome Extension**: Browser extension for capturing web pages
- **Android Client**: Mobile app for sharing links from other applications

### Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Database | SQLite with FastLite | Simple deployment, sufficient for medium scale |
| Search | SQLite LIKE | Simple wildcard search, no FTS complexity |
| Multi-tenancy | Single database, user_id isolation | Simpler backup/restore, efficient for medium scale |
| Python version | 3.12+ | Latest features, modern type hints |
| Authentication | OAuth (Google, GitHub) | No password management complexity |

---

## Architecture

### Directory Structure

```
linkjot/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastHTML application entry
│   │   ├── auth.py              # OAuth handlers
│   │   ├── api.py               # JSON API endpoints
│   │   ├── views.py             # HTML views
│   │   ├── models.py            # Database models
│   │   ├── db.py                # FastLite database setup
│   │   └── cli.py               # Admin CLI commands
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── test_api.py
│   │   ├── test_auth.py
│   │   └── test_views.py
│   ├── requirements.txt
│   └── setup.py
├── clients/
│   ├── android/
│   │   ├── app/
│   │   │   ├── src/main/java/
│   │   │   └── src/test/java/
│   │   ├── build.gradle
│   │   └── README.md
│   └── chrome-extension/
│       ├── manifest.json
│       ├── popup/
│       ├── background/
│       ├── tests/
│       └── README.md
├── docs/
│   ├── api.md
│   ├── deployment.md
│   └── self-hosting.md
├── .env.example
└── README.md
```

---

## Backend

### Technology Stack

- **Framework**: FastHTML (https://www.fastht.ml/)
- **Database**: SQLite via FastLite (https://github.com/AnswerDotAI/fastlite)
- **CSS**: DaisyUI via CDN (https://daisyui.com/)
- **Python**: 3.12+

### Configuration

Configuration via environment variables with `.env` file support (python-dotenv):

```bash
# Required for OAuth
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GITHUB_CLIENT_ID=...
GITHUB_CLIENT_SECRET=...

# Application
SECRET_KEY=...                    # For session signing
DATABASE_PATH=./linkjot.db        # SQLite database location
BASE_URL=https://linkjot.example.com

# Rate limiting
RATE_LIMIT_REQUESTS=100           # Requests per window
RATE_LIMIT_WINDOW=60              # Window in seconds
```

### CLI Reference

The `linkjot` CLI provides administrative commands for database management, user operations, and maintenance tasks. All commands support `--help` for usage details.

```bash
linkjot --help               # Show all commands
linkjot --version            # Show version
```

#### Database Commands

```bash
linkjot db init
```
Initialize database schema. Creates all tables, indexes, triggers, and FTS virtual tables. Safe to run on existing database (no-op if already initialized).

```bash
linkjot db migrate
```
Run pending database migrations. Applies any schema changes for version upgrades.

```bash
linkjot db backup <path>
```
Create a backup of the database to the specified path. Uses SQLite's backup API for safe hot backups.

**Options:**
- `<path>` - Destination file path (required)

**Example:**
```bash
linkjot db backup /backups/linkjot-2024-01-15.db
```

#### User Commands

```bash
linkjot user list [--format FORMAT]
```
List all users with summary statistics.

**Options:**
- `--format` - Output format: `table` (default), `json`, `csv`

**Output columns:** ID, Email, Provider, Created, Bookmarks, Tags, Status

```bash
linkjot user info <email>
```
Show detailed information for a specific user.

**Output:** Email, provider, created date, bookmark count, tag count, session count, token count, premium status, admin status, suspension status.

```bash
linkjot user export <email> [--output PATH]
```
Export a user's bookmarks as JSON. For admin data portability requests.

**Options:**
- `--output` - Output file path (default: stdout)

**Example:**
```bash
linkjot user export user@example.com --output /tmp/export.json
```

```bash
linkjot user delete <email> [--force]
```
Permanently delete a user and all their data (bookmarks, tags, sessions, tokens).

**Options:**
- `--force` - Skip confirmation prompt

```bash
linkjot user suspend <email> --reason <reason>
```
Suspend a user account. Terminates all active sessions and blocks login.

**Options:**
- `--reason` - Required suspension reason (stored in database)

**Example:**
```bash
linkjot user suspend spammer@example.com --reason "ToS violation: spam"
```

```bash
linkjot user unsuspend <email>
```
Remove suspension from a user account, allowing login again.

#### Admin Commands

```bash
linkjot admin init <email>
```
Bootstrap the first admin user. Only works when no admin users exist. Use this for initial setup.

```bash
linkjot admin grant <email>
```
Grant admin privileges to an existing user.

```bash
linkjot admin revoke <email>
```
Revoke admin privileges from a user. Cannot revoke the last admin.

```bash
linkjot admin list
```
List all admin users.

#### Maintenance Commands

```bash
linkjot cleanup sessions [--dry-run]
```
Remove expired sessions from the database.

**Options:**
- `--dry-run` - Show what would be deleted without deleting

```bash
linkjot cleanup tokens [--dry-run]
```
Remove expired API tokens from the database.

**Options:**
- `--dry-run` - Show what would be deleted without deleting

```bash
linkjot stats
```
Display database statistics.

**Output:**
- Total users (all, premium, admin, suspended)
- Total bookmarks
- Total tags
- Total active sessions
- Total API tokens
- Database file size
- FTS index size

#### Token Commands

```bash
linkjot token create <email> --name <name> --scope <scope> [--expires <days>]
```
Create an API token for a user (for automated/service accounts).

**Options:**
- `--name` - Token name (required)
- `--scope` - Token scope: `read` or `write` (required)
- `--expires` - Days until expiration (default: 365)

**Output:** Prints the token value (only shown once).

**Example:**
```bash
linkjot token create service@example.com --name "CI Pipeline" --scope write --expires 90
```

```bash
linkjot token list <email>
```
List all API tokens for a user (shows names and expiry, not token values).

```bash
linkjot token revoke <email> --name <name>
```
Revoke a specific API token by name.

#### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Invalid arguments |
| 3 | User not found |
| 4 | Database error |
| 5 | Permission denied |

### Health Check

Simple health endpoint at `GET /health`:

```json
{"status": "ok"}
```

Returns HTTP 200 if server is running.

### Logging

Standard request/response logging in production:

- All HTTP requests with method, path, status, duration
- All errors with stack traces
- Authentication events (login, logout, token creation)

Format: Plain text logs to stdout (compatible with systemd journald).

---

## Clients

### Chrome Extension

**Manifest Version**: V3 (Chrome's current standard)

**Features**:
- Capture current page URL via toolbar button
- Capture links via right-click context menu
- Full bookmark form in popup (URL, title, tags, comment)
- Settings page to configure backend URL (defaults to hosted instance)

**Authentication Flow**:
- Login required before any functionality
- Opens backend OAuth flow in new tab
- Receives session token via redirect back to extension

**Permissions Required**:
- `activeTab` - Access current tab URL/title
- `contextMenus` - Right-click menu integration
- `storage` - Store settings and session
- `identity` - OAuth flow handling

### Android Client

**Language**: Java
**Minimum API Level**: 29 (Android 10)

**Features**:
- Share intent receiver for URLs from other apps
- Bottom sheet UI for quick capture (expandable for more space)
- Full bookmark form: URL, title, tags (from managed vocabulary), comment
- Settings for backend URL configuration

**Authentication Flow**:
- Browser redirect OAuth (opens system browser)
- Deep link callback to return to app
- Secure token storage in Android Keystore

**Permissions Required**:
- `INTERNET` - API communication
- None else required

---

## Data Model

### Database Schema

```sql
-- Users table
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    email TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_premium BOOLEAN DEFAULT FALSE,
    is_admin BOOLEAN DEFAULT FALSE,
    is_suspended BOOLEAN DEFAULT FALSE,
    suspended_at TIMESTAMP,
    suspended_reason TEXT
);

-- OAuth credentials (separate from users for multi-provider support)
CREATE TABLE credentials (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider TEXT NOT NULL,           -- 'google' or 'github'
    provider_user_id TEXT NOT NULL,   -- ID from OAuth provider
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(provider, provider_user_id)
);

-- Note: Each OAuth provider creates a SEPARATE user account
-- No automatic linking by email

-- Sessions for web UI and clients
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,              -- Random session token
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    last_activity_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_agent TEXT,                  -- For device identification
    client_name TEXT,                 -- 'web', 'chrome-extension', 'android'
    ip_address TEXT
);

-- API tokens
CREATE TABLE api_tokens (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,               -- User-provided name
    token_hash TEXT NOT NULL UNIQUE,  -- SHA-256 hash of token
    scope TEXT NOT NULL DEFAULT 'read', -- 'read' or 'write'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    last_used_at TIMESTAMP
);

-- Tags (managed vocabulary per user)
CREATE TABLE tags (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    color TEXT DEFAULT '#6b7280',     -- Hex color code
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, name)
);

-- Bookmarks
CREATE TABLE bookmarks (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    title TEXT,
    comment TEXT,
    client_name TEXT,                 -- 'web', 'chrome-extension', 'android'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Note: Duplicate URLs ARE allowed (same user can bookmark same URL multiple times)

-- Bookmark-tag junction table
CREATE TABLE bookmark_tags (
    bookmark_id INTEGER NOT NULL REFERENCES bookmarks(id) ON DELETE CASCADE,
    tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (bookmark_id, tag_id)
);

-- Note: Deleting a tag CASCADE removes it from all bookmarks
```

### Indexes

```sql
CREATE INDEX idx_bookmarks_user_created ON bookmarks(user_id, created_at DESC);
CREATE INDEX idx_bookmarks_user_url ON bookmarks(user_id, url);
CREATE INDEX idx_tags_user ON tags(user_id);
CREATE INDEX idx_sessions_expires ON sessions(expires_at);
CREATE INDEX idx_api_tokens_expires ON api_tokens(expires_at);
```

---

## API Specification

All API endpoints require authentication via API token in header:

```
Authorization: Bearer <api_token>
```

### Base URL

```
POST /api/v1/<endpoint>
```

All endpoints use POST with JSON body (even for queries). Responses are JSON.

### Error Format

```json
{
    "error": "Human readable message",
    "code": "ERROR_CODE"
}
```

Error codes:
- `INVALID_TOKEN` - Token missing, invalid, or expired
- `PERMISSION_DENIED` - Token lacks required scope
- `VALIDATION_ERROR` - Invalid request body
- `NOT_FOUND` - Resource not found
- `RATE_LIMITED` - Too many requests
- `LIMIT_EXCEEDED` - Free tier limit reached

### Endpoints

#### Bookmarks

**Add Bookmark** (requires `write` scope)

```
POST /api/v1/bookmarks/add
```

Request:
```json
{
    "url": "https://example.com/article",
    "title": "Example Article",
    "comment": "Interesting read about...",
    "tags": ["tech", "reading-list"],
    "client_name": "chrome-extension"
}
```

Response (201):
```json
{
    "id": 12345,
    "url": "https://example.com/article",
    "title": "Example Article",
    "comment": "Interesting read about...",
    "tags": [
        {"id": 1, "name": "tech", "color": "#3b82f6"},
        {"id": 2, "name": "reading-list", "color": "#10b981"}
    ],
    "client_name": "chrome-extension",
    "created_at": "2024-01-15T10:30:00Z"
}
```

Note: If a tag name doesn't exist in user's vocabulary, it is automatically created with default color.

**Edit Bookmark** (requires `write` scope)

```
POST /api/v1/bookmarks/edit
```

Request:
```json
{
    "id": 12345,
    "title": "Updated Title",
    "comment": "Updated comment",
    "tags": ["tech", "important"]
}
```

Response (200): Same format as add.

**Delete Bookmark** (requires `write` scope)

```
POST /api/v1/bookmarks/delete
```

Request:
```json
{
    "id": 12345
}
```

Response (200):
```json
{
    "deleted": true
}
```

**Search Bookmarks** (requires `read` scope)

```
POST /api/v1/bookmarks/search
```

Request:
```json
{
    "query": "python tutorial",
    "tags": ["tech"],
    "page": 1,
    "per_page": 50
}
```

All fields optional. Results sorted by `created_at` DESC (newest first).

Response (200):
```json
{
    "bookmarks": [
        {
            "id": 12345,
            "url": "https://example.com",
            "title": "Python Tutorial",
            "comment": "Great beginner resource",
            "tags": [{"id": 1, "name": "tech", "color": "#3b82f6"}],
            "client_name": "web",
            "created_at": "2024-01-15T10:30:00Z"
        }
    ],
    "total": 150,
    "page": 1,
    "per_page": 50,
    "has_more": true,
    "next_cursor": "eyJpZCI6MTIzNDV9"
}
```

Pagination:
- UI/browsing: Use `page` + `per_page` (offset-based)
- API automation: Use `cursor` for efficient iteration over large datasets

**List Bookmarks** (requires `read` scope)

```
POST /api/v1/bookmarks/list
```

Request:
```json
{
    "cursor": null,
    "limit": 100
}
```

Response: Same format as search, cursor-based pagination only.

#### Tags

**List Tags** (requires `read` scope)

```
POST /api/v1/tags/list
```

Response (200):
```json
{
    "tags": [
        {"id": 1, "name": "tech", "color": "#3b82f6", "bookmark_count": 42},
        {"id": 2, "name": "reading-list", "color": "#10b981", "bookmark_count": 15}
    ]
}
```

**Create Tag** (requires `write` scope)

```
POST /api/v1/tags/create
```

Request:
```json
{
    "name": "work",
    "color": "#f59e0b"
}
```

**Update Tag** (requires `write` scope)

```
POST /api/v1/tags/update
```

Request:
```json
{
    "id": 1,
    "name": "technology",
    "color": "#6366f1"
}
```

**Delete Tag** (requires `write` scope)

```
POST /api/v1/tags/delete
```

Request:
```json
{
    "id": 1
}
```

Note: Deleting a tag removes it from all bookmarks (cascade).

#### Export

**Export All Bookmarks** (requires `read` scope)

```
POST /api/v1/export
```

Request:
```json
{
    "format": "json"
}
```

Response: JSON array of all user's bookmarks with tags.

### Rate Limiting

Basic per-minute rate limiting:
- Default: 100 requests per 60 seconds per API token
- Returns `429 Too Many Requests` with `Retry-After` header when exceeded

---

## Authentication & Authorization

### OAuth Providers

Supported providers:
- **Google** - Using Google Sign-In
- **GitHub** - Using GitHub OAuth Apps

Each provider login creates a **separate user account**. No automatic linking by email.

#### Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)

2. Create a new project or select an existing one

3. Navigate to **APIs & Services > Credentials**

4. Click **Create Credentials > OAuth client ID**

5. If prompted, configure the OAuth consent screen:
   - User Type: External (or Internal for Google Workspace)
   - App name: LinkJot
   - User support email: your email
   - Authorized domains: your domain (e.g., `linkjot.example.com`)
   - Developer contact: your email

6. For the OAuth client:
   - Application type: **Web application**
   - Name: LinkJot Web
   - Authorized JavaScript origins:
     - `http://localhost:5001` (development)
     - `https://linkjot.example.com` (production)
   - Authorized redirect URIs:
     - `http://localhost:5001/auth_redirect/google` (development)
     - `https://linkjot.example.com/auth_redirect/google` (production)

7. Copy the **Client ID** and **Client Secret** to your `.env` file:
   ```
   GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=your-client-secret
   ```

#### GitHub OAuth Setup

1. Go to [GitHub Developer Settings](https://github.com/settings/developers)

2. Click **OAuth Apps > New OAuth App**

3. Fill in the application details:
   - Application name: LinkJot
   - Homepage URL: `http://localhost:5001` (or your production URL)
   - Application description: Bookmark management application
   - Authorization callback URL: `http://localhost:5001/auth_redirect/github`

4. Click **Register application**

5. On the app page, click **Generate a new client secret**

6. Copy the **Client ID** and **Client Secret** to your `.env` file:
   ```
   GITHUB_CLIENT_ID=your-client-id
   GITHUB_CLIENT_SECRET=your-client-secret
   ```

**Note for production:** Update the callback URLs to use your production domain with HTTPS.

#### Testing OAuth Locally

For local development:
1. Ensure `BASE_URL=http://localhost:5001` in your `.env`
2. The OAuth redirect URIs must exactly match what's configured in the provider
3. Google requires localhost, not 127.0.0.1
4. GitHub works with either localhost or 127.0.0.1

### Session Management

- **Lifetime**: Long-lived (configurable, default 30 days)
- **Multi-device**: Users can have multiple active sessions simultaneously
- **Storage**: Secure HTTP-only cookies with SameSite=Strict

### API Tokens

- **Scopes**: `read` (search, list, export) or `write` (add, edit, delete, plus all read operations)
- **Expiration**: Default 1 year, configurable 30 days to never
- **Display**: Token shown once at creation, stored as SHA-256 hash
- **Naming**: User provides a name for each token (e.g., "Chrome Extension", "Android Phone")

### CSRF Protection

Double-submit cookie pattern:
- CSRF token stored in cookie
- Must be included in form submissions
- Validated server-side

---

## User Interface

### Web UI (FastHTML + DaisyUI)

#### Theme

- Follows system preference (prefers-color-scheme)
- DaisyUI light/dark themes via CDN

#### Layout

**Main bookmark list**:
- Compact list view (one bookmark per row)
- Columns: checkbox, title (linked), URL domain, tags, date, actions
- Supports bulk selection via checkboxes
- Pagination at bottom

**Bulk operations** (when items selected):
- Delete selected
- Add tag to selected
- Remove tag from selected
- Export selected

#### Keyboard Navigation

Full vim-style keyboard shortcuts:

| Key | Action |
|-----|--------|
| `/` | Focus search input |
| `j` | Move to next bookmark |
| `k` | Move to previous bookmark |
| `Enter` | Open selected bookmark |
| `o` | Open bookmark in new tab |
| `x` | Toggle selection |
| `d` | Delete selected (with confirmation) |
| `t` | Open tag picker for selected |
| `g` `g` | Go to first bookmark |
| `G` | Go to last bookmark |
| `?` | Show keyboard shortcut help |
| `Esc` | Clear selection / close modals |

#### Pages

- `/` - Bookmark list with search
- `/settings` - User profile, tag management, API tokens
- `/settings/tags` - Manage tag vocabulary (create, rename, delete, set colors)
- `/settings/tokens` - Manage API tokens
- `/settings/sessions` - View and manage active sessions
- `/login` - OAuth provider selection
- `/export` - Download bookmarks as JSON

#### Session Management (`/settings/sessions`)

Users can view all active sessions (web UI and client authentications):

**Session list displays**:
- Device/client name (derived from user agent or client_name)
- IP address (last known)
- Login date
- Last activity date
- "Current session" indicator for the active session
- Revoke button for each session (except current, or with confirmation)

**Actions**:
- Revoke individual session (immediately invalidates that session)
- "Revoke all other sessions" button (keeps current session active)

### Admin UI

Admin interface for users with `is_admin = TRUE`. Accessible only to admins.

**Privacy constraint**: Admins can see aggregate statistics but **CANNOT view, search, or access any user's personal bookmarks or bookmark content**. This is enforced at the database query level.

#### Admin Pages

- `/admin` - Dashboard with system statistics
- `/admin/users` - User management list
- `/admin/users/:id` - Individual user details

#### Admin Dashboard (`/admin`)

System-wide statistics:
- Total users (all-time, last 30 days, last 7 days)
- Total bookmarks across all users
- Total active sessions
- Storage usage (database size)

#### User Management (`/admin/users`)

Paginated, searchable list of all users.

**List columns**:
- Email
- OAuth provider
- Created date
- Bookmark count (aggregate only)
- Tag count (aggregate only)
- Session count (active)
- Status (active/suspended)
- Premium status
- Actions

**Search/filter**:
- Search by email
- Filter by status (all, active, suspended)
- Filter by premium status
- Sort by created date, bookmark count, last activity

#### User Details (`/admin/users/:id`)

**Visible information**:
- Email address
- OAuth provider
- Account created date
- Last login date
- Bookmark count (number only, not content)
- Tag count (number only, not names)
- Active session count
- API token count
- Premium status
- Suspension status and reason (if applicable)

**Admin actions**:
- Toggle premium status
- Suspend user (with reason) - terminates all sessions, blocks login
- Unsuspend user
- Delete user (with confirmation) - immediate hard delete of all data
- Terminate all user sessions

**Explicitly NOT available to admins**:
- View user's bookmarks or bookmark content
- View user's tags or tag names
- View user's API token names or values
- View user's session details (only count)
- Export user's data

See [CLI Reference](#cli-reference) for admin command-line operations.

### Chrome Extension

**Popup UI**:
- Backend URL indicator (configurable in options)
- Login button (if not authenticated)
- When authenticated:
  - Current page URL (pre-filled)
  - Title input (pre-filled from page)
  - Tag selector (multi-select from vocabulary)
  - Comment textarea
  - Save button

**Options page**:
- Backend URL input (default: hosted instance)
- Current login status
- Logout button

**Context menu**:
- "Save to LinkJot" on link right-click
- Opens popup pre-filled with link URL

### Android Client

**Share sheet integration**:
- Appears as share target for URLs
- Opens bottom sheet overlay

**Bottom sheet UI** (default state):
- URL (read-only, from share intent)
- Title input
- Quick tag chips (most used)
- Save button
- Expand button

**Expanded state**:
- Full tag picker
- Comment textarea
- More space for longer titles

**Settings activity**:
- Backend URL configuration
- Account info
- Logout option

---

## Testing Strategy

### Backend Tests

**Framework**: pytest with FastHTML TestClient

**Test database**: In-memory SQLite (`:memory:`)

**Coverage areas**:
- API endpoints (all CRUD operations)
- Authentication flows (OAuth mocking)
- Authorization (scope enforcement)
- Full-text search accuracy
- Rate limiting behavior
- Pagination correctness
- Data validation

**Running tests**:
```bash
cd backend
pytest tests/ -v
```

### Chrome Extension Tests

**Framework**: Playwright with Chrome extension loading

**Approach**: Mock API (service worker interception)

**Coverage areas**:
- Popup form submission
- Context menu functionality
- Options page configuration
- OAuth flow (mocked)
- Error handling

**Running tests**:
```bash
cd clients/chrome-extension
npm test
```

### Android Tests

**Framework**: JUnit

**Approach**: Unit tests for business logic, mock network calls

**Coverage areas**:
- API client methods
- Data parsing
- Form validation
- Token storage/retrieval

**Running tests**:
```bash
cd clients/android
./gradlew test
```

### Test Data Management

Each test module should:
1. Create isolated test user
2. Set up required test data
3. Clean up after test (automatic with in-memory DB)

Example fixture:
```python
@pytest.fixture
def test_user(client):
    """Create a test user with API token."""
    # Create user, return token for API calls
    ...
```

---

## Deployment

### Self-Hosting (Bare Python + systemd)

**Prerequisites**:
- Python 3.12+
- systemd (Linux)

**Installation**:

```bash
# Clone repository
git clone https://github.com/your-org/linkjot.git
cd linkjot/backend

# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your OAuth credentials and settings

# Initialize database
python -m app.cli db init

# Run (development)
python -m app.main
```

**systemd service** (`/etc/systemd/system/linkjot.service`):

```ini
[Unit]
Description=LinkJot Bookmark Manager
After=network.target

[Service]
Type=simple
User=linkjot
WorkingDirectory=/opt/linkjot/backend
Environment=PATH=/opt/linkjot/backend/venv/bin
EnvironmentFile=/opt/linkjot/backend/.env
ExecStart=/opt/linkjot/backend/venv/bin/python -m app.main
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

**Enable and start**:
```bash
sudo systemctl daemon-reload
sudo systemctl enable linkjot
sudo systemctl start linkjot
```

**Reverse proxy** (nginx example):

```nginx
server {
    listen 443 ssl http2;
    server_name linkjot.example.com;

    ssl_certificate /etc/letsencrypt/live/linkjot.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/linkjot.example.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Backups

SQLite file backup strategy:

```bash
# Create backup (while app is running - SQLite handles this safely)
sqlite3 /opt/linkjot/backend/linkjot.db ".backup '/backups/linkjot-$(date +%Y%m%d).db'"

# Cron job (daily at 2 AM)
0 2 * * * /usr/bin/sqlite3 /opt/linkjot/backend/linkjot.db ".backup '/backups/linkjot-$(date +\%Y\%m\%d).db'"
```

Backup retention: Keep last 7 daily, 4 weekly, 12 monthly.

---

## Hosted Instance

### Service Model

**Free tier** (default):
- 1,000 bookmarks maximum
- 50 tags maximum
- Full functionality within limits

**Premium tier** (future):
- Unlimited bookmarks
- Unlimited tags
- Priority support

### Infrastructure

- Single server deployment (sufficient for medium scale 100-1000 users)
- Standard logging (requests + errors)
- SQLite file backups (daily)
- Health check monitoring at `/health`

### Client Defaults

Both Chrome extension and Android client default to connecting to the hosted instance. Users can change the backend URL in settings for self-hosted deployments.

---

## Future Considerations

These features are explicitly **out of scope** for initial implementation but documented for potential future work:

- **Page archiving**: Storing actual page content
- **Dead link detection**: Checking if bookmarked URLs are still accessible
- **Search operators**: Advanced query syntax (tag:x, before:date)
- **Account linking**: Connecting multiple OAuth providers to one account
- **Semantic search**: AI-powered meaning-based search
- **Browser bookmark import**: Import from Chrome/Firefox bookmark files
- **Other service import**: Import from Pocket, Pinboard, etc.

---

## Appendix: External Documentation

- FastHTML: https://www.fastht.ml/docs/llms.txt
- DaisyUI: https://daisyui.com/docs/install/
- FastLite: https://github.com/AnswerDotAI/fastlite
- Chrome Extension MV3: https://developer.chrome.com/docs/extensions/mv3/
