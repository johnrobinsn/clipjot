"""API Documentation Data.

This module defines the canonical documentation for all API endpoints.
It serves as the single source of truth for:
- /docs/api/* routes for HTML documentation
- /llms.txt and /llms-full.txt for LLM-readable docs
- Future: OpenAPI spec generation
"""

API_VERSION = "v1"
API_BASE_PATH = "/api/v1"

# =============================================================================
# API Sections
# =============================================================================

SECTIONS = [
    {
        "id": "overview",
        "title": "Overview",
        "icon": "book-open",
    },
    {
        "id": "auth",
        "title": "Authentication",
        "icon": "key",
    },
    {
        "id": "bookmarks",
        "title": "Bookmarks",
        "icon": "bookmark",
    },
    {
        "id": "tags",
        "title": "Tags",
        "icon": "tag",
    },
    {
        "id": "data",
        "title": "Import & Export",
        "icon": "arrow-down-tray",
    },
    {
        "id": "errors",
        "title": "Errors",
        "icon": "exclamation-triangle",
    },
    {
        "id": "rate-limits",
        "title": "Rate Limits",
        "icon": "clock",
    },
]

# =============================================================================
# Endpoint Definitions
# =============================================================================

ENDPOINTS = {
    # Authentication
    "auth/invite": {
        "section": "auth",
        "method": "POST",
        "path": "/api/v1/auth/invite",
        "scope": None,  # Public endpoint
        "summary": "Authenticate with invite code",
        "description": "Exchange an invite code for a session token. This is a public endpoint that does not require authentication.",
        "request_schema": {
            "code": {"type": "string", "required": True, "description": "8-character invite code (uppercase alphanumeric)"},
        },
        "response_schema": {
            "token": {"type": "string", "description": "Session token for API authentication"},
            "user": {"type": "object", "description": "User object with id and email"},
        },
        "examples": {
            "curl": '''curl -X POST https://your-domain.com/api/v1/auth/invite \\
  -H "Content-Type: application/json" \\
  -d '{"code": "ABC12345"}'
''',
            "python": '''import requests

response = requests.post(
    "https://your-domain.com/api/v1/auth/invite",
    json={"code": "ABC12345"}
)
data = response.json()
token = data["token"]
''',
            "javascript": '''const response = await fetch('/api/v1/auth/invite', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ code: 'ABC12345' })
});
const { token, user } = await response.json();
''',
        },
    },

    "logout": {
        "section": "auth",
        "method": "POST",
        "path": "/api/v1/logout",
        "scope": "read",
        "summary": "Logout and revoke session",
        "description": "Revokes the current session token, logging out the user.",
        "request_schema": {},
        "response_schema": {
            "logged_out": {"type": "boolean", "description": "Always true on success"},
            "message": {"type": "string", "description": "Confirmation message"},
        },
        "examples": {
            "curl": '''curl -X POST https://your-domain.com/api/v1/logout \\
  -H "Authorization: Bearer $TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{}'
''',
            "python": '''import requests

response = requests.post(
    "https://your-domain.com/api/v1/logout",
    headers={"Authorization": f"Bearer {token}"},
    json={}
)
''',
            "javascript": '''await fetch('/api/v1/logout', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({})
});
''',
        },
    },

    # Bookmarks
    "bookmarks/add": {
        "section": "bookmarks",
        "method": "POST",
        "path": "/api/v1/bookmarks/add",
        "scope": "write",
        "summary": "Create a new bookmark",
        "description": "Add a new bookmark with optional title, comment, and tags. Tags are created automatically if they don't exist.",
        "request_schema": {
            "url": {"type": "string", "required": True, "description": "The URL to bookmark"},
            "title": {"type": "string", "required": False, "description": "Display title (optional)"},
            "comment": {"type": "string", "required": False, "description": "Personal note or comment (optional)"},
            "tags": {"type": "array", "required": False, "description": "List of tag names (optional)"},
        },
        "response_schema": {
            "id": {"type": "integer", "description": "Unique bookmark ID"},
            "url": {"type": "string", "description": "The bookmarked URL"},
            "title": {"type": "string", "description": "Display title"},
            "comment": {"type": "string", "description": "Personal note"},
            "tags": {"type": "array", "description": "List of tag objects"},
            "created_at": {"type": "string", "description": "ISO 8601 timestamp"},
            "updated_at": {"type": "string", "description": "ISO 8601 timestamp"},
        },
        "examples": {
            "curl": '''curl -X POST https://your-domain.com/api/v1/bookmarks/add \\
  -H "Authorization: Bearer $TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "url": "https://example.com/article",
    "title": "Interesting Article",
    "comment": "Read this later",
    "tags": ["reading", "tech"]
  }'
''',
            "python": '''import requests

response = requests.post(
    "https://your-domain.com/api/v1/bookmarks/add",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "url": "https://example.com/article",
        "title": "Interesting Article",
        "comment": "Read this later",
        "tags": ["reading", "tech"]
    }
)
bookmark = response.json()
''',
            "javascript": '''const response = await fetch('/api/v1/bookmarks/add', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    url: 'https://example.com/article',
    title: 'Interesting Article',
    comment: 'Read this later',
    tags: ['reading', 'tech']
  })
});
const bookmark = await response.json();
''',
        },
    },

    "bookmarks/edit": {
        "section": "bookmarks",
        "method": "POST",
        "path": "/api/v1/bookmarks/edit",
        "scope": "write",
        "summary": "Update an existing bookmark",
        "description": "Update the title, comment, or tags of an existing bookmark. Only provided fields are updated.",
        "request_schema": {
            "id": {"type": "integer", "required": True, "description": "Bookmark ID to update"},
            "title": {"type": "string", "required": False, "description": "New title (optional)"},
            "comment": {"type": "string", "required": False, "description": "New comment (optional)"},
            "tags": {"type": "array", "required": False, "description": "New tag list (replaces existing tags)"},
        },
        "response_schema": {
            "id": {"type": "integer", "description": "Bookmark ID"},
            "url": {"type": "string", "description": "The bookmarked URL"},
            "title": {"type": "string", "description": "Updated title"},
            "comment": {"type": "string", "description": "Updated comment"},
            "tags": {"type": "array", "description": "Updated tag list"},
            "updated_at": {"type": "string", "description": "ISO 8601 timestamp"},
        },
        "examples": {
            "curl": '''curl -X POST https://your-domain.com/api/v1/bookmarks/edit \\
  -H "Authorization: Bearer $TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "id": 123,
    "title": "Updated Title",
    "tags": ["important", "work"]
  }'
''',
            "python": '''import requests

response = requests.post(
    "https://your-domain.com/api/v1/bookmarks/edit",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "id": 123,
        "title": "Updated Title",
        "tags": ["important", "work"]
    }
)
bookmark = response.json()
''',
            "javascript": '''const response = await fetch('/api/v1/bookmarks/edit', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    id: 123,
    title: 'Updated Title',
    tags: ['important', 'work']
  })
});
const bookmark = await response.json();
''',
        },
    },

    "bookmarks/delete": {
        "section": "bookmarks",
        "method": "POST",
        "path": "/api/v1/bookmarks/delete",
        "scope": "write",
        "summary": "Delete a bookmark",
        "description": "Permanently delete a bookmark by ID.",
        "request_schema": {
            "id": {"type": "integer", "required": True, "description": "Bookmark ID to delete"},
        },
        "response_schema": {
            "deleted": {"type": "boolean", "description": "Always true on success"},
        },
        "examples": {
            "curl": '''curl -X POST https://your-domain.com/api/v1/bookmarks/delete \\
  -H "Authorization: Bearer $TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{"id": 123}'
''',
            "python": '''import requests

response = requests.post(
    "https://your-domain.com/api/v1/bookmarks/delete",
    headers={"Authorization": f"Bearer {token}"},
    json={"id": 123}
)
''',
            "javascript": '''await fetch('/api/v1/bookmarks/delete', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ id: 123 })
});
''',
        },
    },

    "bookmarks/search": {
        "section": "bookmarks",
        "method": "POST",
        "path": "/api/v1/bookmarks/search",
        "scope": "read",
        "summary": "Search bookmarks",
        "description": "Search bookmarks by query string with pagination. Searches URL, title, and comment fields.",
        "request_schema": {
            "query": {"type": "string", "required": False, "description": "Search query (searches URL, title, comment)"},
            "tag": {"type": "string", "required": False, "description": "Filter by tag name"},
            "page": {"type": "integer", "required": False, "description": "Page number (default: 1)"},
            "per_page": {"type": "integer", "required": False, "description": "Results per page (default: 50, max: 100)"},
        },
        "response_schema": {
            "bookmarks": {"type": "array", "description": "List of bookmark objects"},
            "total": {"type": "integer", "description": "Total matching bookmarks"},
            "page": {"type": "integer", "description": "Current page number"},
            "per_page": {"type": "integer", "description": "Results per page"},
            "has_more": {"type": "boolean", "description": "Whether more results exist"},
        },
        "examples": {
            "curl": '''curl -X POST https://your-domain.com/api/v1/bookmarks/search \\
  -H "Authorization: Bearer $TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "query": "python tutorial",
    "page": 1,
    "per_page": 20
  }'
''',
            "python": '''import requests

response = requests.post(
    "https://your-domain.com/api/v1/bookmarks/search",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "query": "python tutorial",
        "page": 1,
        "per_page": 20
    }
)
results = response.json()
bookmarks = results["bookmarks"]
''',
            "javascript": '''const response = await fetch('/api/v1/bookmarks/search', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    query: 'python tutorial',
    page: 1,
    per_page: 20
  })
});
const { bookmarks, total, has_more } = await response.json();
''',
        },
    },

    "bookmarks/list": {
        "section": "bookmarks",
        "method": "POST",
        "path": "/api/v1/bookmarks/list",
        "scope": "read",
        "summary": "List all bookmarks",
        "description": "Get all bookmarks with cursor-based pagination. Use for full sync or bulk operations.",
        "request_schema": {
            "cursor": {"type": "string", "required": False, "description": "Pagination cursor from previous response"},
            "limit": {"type": "integer", "required": False, "description": "Max results (default: 100, max: 500)"},
        },
        "response_schema": {
            "bookmarks": {"type": "array", "description": "List of bookmark objects"},
            "has_more": {"type": "boolean", "description": "Whether more results exist"},
            "next_cursor": {"type": "string", "description": "Cursor for next page (if has_more is true)"},
        },
        "examples": {
            "curl": '''curl -X POST https://your-domain.com/api/v1/bookmarks/list \\
  -H "Authorization: Bearer $TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{"limit": 100}'
''',
            "python": '''import requests

# Fetch all bookmarks with pagination
all_bookmarks = []
cursor = None

while True:
    response = requests.post(
        "https://your-domain.com/api/v1/bookmarks/list",
        headers={"Authorization": f"Bearer {token}"},
        json={"cursor": cursor, "limit": 100}
    )
    data = response.json()
    all_bookmarks.extend(data["bookmarks"])

    if not data["has_more"]:
        break
    cursor = data["next_cursor"]
''',
            "javascript": '''// Fetch all bookmarks with pagination
const allBookmarks = [];
let cursor = null;

while (true) {
  const response = await fetch('/api/v1/bookmarks/list', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ cursor, limit: 100 })
  });
  const data = await response.json();
  allBookmarks.push(...data.bookmarks);

  if (!data.has_more) break;
  cursor = data.next_cursor;
}
''',
        },
    },

    "bookmarks/sync": {
        "section": "bookmarks",
        "method": "POST",
        "path": "/api/v1/bookmarks/sync",
        "scope": "read",
        "summary": "Incremental sync with long polling",
        "description": "Get new bookmarks since a cursor position. Supports long polling to wait for changes.",
        "request_schema": {
            "cursor": {"type": "integer", "required": False, "description": "Last seen bookmark ID (0 for initial sync)"},
            "limit": {"type": "integer", "required": False, "description": "Max results (default: 50, max: 100)"},
            "wait": {"type": "boolean", "required": False, "description": "Enable long polling (wait up to 30s for new data)"},
        },
        "response_schema": {
            "bookmarks": {"type": "array", "description": "New bookmarks since cursor"},
            "cursor": {"type": "integer", "description": "New cursor position"},
            "has_more": {"type": "boolean", "description": "Whether more results exist"},
            "waited": {"type": "boolean", "description": "Whether request waited (long polling)"},
        },
        "examples": {
            "curl": '''# Initial sync
curl -X POST https://your-domain.com/api/v1/bookmarks/sync \\
  -H "Authorization: Bearer $TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{"cursor": 0}'

# Long polling for changes
curl -X POST https://your-domain.com/api/v1/bookmarks/sync \\
  -H "Authorization: Bearer $TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{"cursor": 123, "wait": true}'
''',
            "python": '''import requests

# Initial sync
response = requests.post(
    "https://your-domain.com/api/v1/bookmarks/sync",
    headers={"Authorization": f"Bearer {token}"},
    json={"cursor": 0}
)
data = response.json()
cursor = data["cursor"]

# Long polling for changes
response = requests.post(
    "https://your-domain.com/api/v1/bookmarks/sync",
    headers={"Authorization": f"Bearer {token}"},
    json={"cursor": cursor, "wait": True},
    timeout=35  # Slightly longer than server wait
)
''',
            "javascript": '''// Initial sync
let response = await fetch('/api/v1/bookmarks/sync', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ cursor: 0 })
});
let data = await response.json();
let cursor = data.cursor;

// Long polling for changes
response = await fetch('/api/v1/bookmarks/sync', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ cursor, wait: true })
});
''',
        },
    },

    # Tags
    "tags/list": {
        "section": "tags",
        "method": "POST",
        "path": "/api/v1/tags/list",
        "scope": "read",
        "summary": "List all tags",
        "description": "Get all tags for the current user with bookmark counts.",
        "request_schema": {},
        "response_schema": {
            "tags": {"type": "array", "description": "List of tag objects with id, name, and bookmark_count"},
        },
        "examples": {
            "curl": '''curl -X POST https://your-domain.com/api/v1/tags/list \\
  -H "Authorization: Bearer $TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{}'
''',
            "python": '''import requests

response = requests.post(
    "https://your-domain.com/api/v1/tags/list",
    headers={"Authorization": f"Bearer {token}"},
    json={}
)
tags = response.json()["tags"]
''',
            "javascript": '''const response = await fetch('/api/v1/tags/list', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({})
});
const { tags } = await response.json();
''',
        },
    },

    "tags/create": {
        "section": "tags",
        "method": "POST",
        "path": "/api/v1/tags/create",
        "scope": "write",
        "summary": "Create a new tag",
        "description": "Create a new tag. Returns error if tag name already exists.",
        "request_schema": {
            "name": {"type": "string", "required": True, "description": "Tag name"},
        },
        "response_schema": {
            "id": {"type": "integer", "description": "Tag ID"},
            "name": {"type": "string", "description": "Tag name"},
            "created_at": {"type": "string", "description": "ISO 8601 timestamp"},
        },
        "examples": {
            "curl": '''curl -X POST https://your-domain.com/api/v1/tags/create \\
  -H "Authorization: Bearer $TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{"name": "recipes"}'
''',
            "python": '''import requests

response = requests.post(
    "https://your-domain.com/api/v1/tags/create",
    headers={"Authorization": f"Bearer {token}"},
    json={"name": "recipes"}
)
tag = response.json()
''',
            "javascript": '''const response = await fetch('/api/v1/tags/create', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ name: 'recipes' })
});
const tag = await response.json();
''',
        },
    },

    "tags/update": {
        "section": "tags",
        "method": "POST",
        "path": "/api/v1/tags/update",
        "scope": "write",
        "summary": "Rename a tag",
        "description": "Update the name of an existing tag.",
        "request_schema": {
            "id": {"type": "integer", "required": True, "description": "Tag ID to update"},
            "name": {"type": "string", "required": True, "description": "New tag name"},
        },
        "response_schema": {
            "id": {"type": "integer", "description": "Tag ID"},
            "name": {"type": "string", "description": "Updated tag name"},
        },
        "examples": {
            "curl": '''curl -X POST https://your-domain.com/api/v1/tags/update \\
  -H "Authorization: Bearer $TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{"id": 5, "name": "cooking"}'
''',
            "python": '''import requests

response = requests.post(
    "https://your-domain.com/api/v1/tags/update",
    headers={"Authorization": f"Bearer {token}"},
    json={"id": 5, "name": "cooking"}
)
tag = response.json()
''',
            "javascript": '''const response = await fetch('/api/v1/tags/update', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ id: 5, name: 'cooking' })
});
const tag = await response.json();
''',
        },
    },

    "tags/delete": {
        "section": "tags",
        "method": "POST",
        "path": "/api/v1/tags/delete",
        "scope": "write",
        "summary": "Delete a tag",
        "description": "Delete a tag. The tag is removed from all bookmarks but bookmarks are not deleted.",
        "request_schema": {
            "id": {"type": "integer", "required": True, "description": "Tag ID to delete"},
        },
        "response_schema": {
            "deleted": {"type": "boolean", "description": "Always true on success"},
        },
        "examples": {
            "curl": '''curl -X POST https://your-domain.com/api/v1/tags/delete \\
  -H "Authorization: Bearer $TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{"id": 5}'
''',
            "python": '''import requests

response = requests.post(
    "https://your-domain.com/api/v1/tags/delete",
    headers={"Authorization": f"Bearer {token}"},
    json={"id": 5}
)
''',
            "javascript": '''await fetch('/api/v1/tags/delete', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ id: 5 })
});
''',
        },
    },

    # Data
    "export": {
        "section": "data",
        "method": "POST",
        "path": "/api/v1/export",
        "scope": "read",
        "summary": "Export all bookmarks",
        "description": "Export all bookmarks as JSON. Includes tags for each bookmark.",
        "request_schema": {},
        "response_schema": {
            "bookmarks": {"type": "array", "description": "All bookmarks with tags"},
            "exported_at": {"type": "string", "description": "ISO 8601 timestamp"},
            "count": {"type": "integer", "description": "Total bookmark count"},
        },
        "examples": {
            "curl": '''curl -X POST https://your-domain.com/api/v1/export \\
  -H "Authorization: Bearer $TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{}' > bookmarks.json
''',
            "python": '''import requests
import json

response = requests.post(
    "https://your-domain.com/api/v1/export",
    headers={"Authorization": f"Bearer {token}"},
    json={}
)
export_data = response.json()

# Save to file
with open("bookmarks.json", "w") as f:
    json.dump(export_data, f, indent=2)
''',
            "javascript": '''const response = await fetch('/api/v1/export', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({})
});
const exportData = await response.json();
console.log(`Exported ${exportData.count} bookmarks`);
''',
        },
    },

    "import": {
        "section": "data",
        "method": "POST",
        "path": "/api/v1/import",
        "scope": "write",
        "summary": "Import bookmarks",
        "description": "Import bookmarks from JSON. Supports merge (skip duplicates) or replace mode.",
        "request_schema": {
            "bookmarks": {"type": "array", "required": True, "description": "Array of bookmark objects to import"},
            "mode": {"type": "string", "required": False, "description": "'merge' (default) or 'replace'"},
        },
        "response_schema": {
            "imported": {"type": "integer", "description": "Number of bookmarks imported"},
            "skipped": {"type": "integer", "description": "Number of duplicates skipped"},
            "errors": {"type": "array", "description": "List of import errors"},
        },
        "examples": {
            "curl": '''curl -X POST https://your-domain.com/api/v1/import \\
  -H "Authorization: Bearer $TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "bookmarks": [
      {"url": "https://example.com", "title": "Example", "tags": ["test"]}
    ],
    "mode": "merge"
  }'
''',
            "python": '''import requests
import json

# Load from file
with open("bookmarks.json", "r") as f:
    export_data = json.load(f)

response = requests.post(
    "https://your-domain.com/api/v1/import",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "bookmarks": export_data["bookmarks"],
        "mode": "merge"
    }
)
result = response.json()
print(f"Imported: {result['imported']}, Skipped: {result['skipped']}")
''',
            "javascript": '''const response = await fetch('/api/v1/import', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    bookmarks: exportData.bookmarks,
    mode: 'merge'
  })
});
const { imported, skipped, errors } = await response.json();
''',
        },
    },
}

# =============================================================================
# Error Codes
# =============================================================================

ERROR_CODES = {
    "INVALID_TOKEN": {
        "status": 401,
        "description": "The provided token is invalid, expired, or missing.",
    },
    "PERMISSION_DENIED": {
        "status": 403,
        "description": "The token does not have the required scope for this operation.",
    },
    "VALIDATION_ERROR": {
        "status": 400,
        "description": "The request body is missing required fields or contains invalid data.",
    },
    "NOT_FOUND": {
        "status": 404,
        "description": "The requested resource (bookmark, tag, etc.) was not found.",
    },
    "RATE_LIMITED": {
        "status": 429,
        "description": "Too many requests. Check the Retry-After header.",
    },
    "LIMIT_EXCEEDED": {
        "status": 403,
        "description": "Account limit reached (e.g., max bookmarks for free tier).",
    },
}

# =============================================================================
# Helper Functions
# =============================================================================

def get_endpoints_by_section(section_id: str) -> list:
    """Get all endpoints for a given section."""
    return [
        {"key": key, **endpoint}
        for key, endpoint in ENDPOINTS.items()
        if endpoint.get("section") == section_id
    ]


def generate_llms_txt(full: bool = False) -> str:
    """Generate llms.txt or llms-full.txt content from endpoint data."""
    lines = [
        "# ClipJot",
        "",
        "> Personal bookmark manager - save links from anywhere, access them everywhere.",
        "",
    ]

    if not full:
        lines.extend([
            "ClipJot is a self-hosted bookmark manager with web UI, REST API, Chrome extension, and Android app.",
            "",
            "## Features",
            "",
            "- Save links from browser extension, mobile app, or web UI",
            "- Organize with tags",
            "- Add notes to bookmarks",
            "- Full-text search",
            "- Export/import data",
            "- OAuth authentication (Google, GitHub)",
            "",
            "## API",
            "",
            "REST API available at /api/v1/ for programmatic access.",
            "API documentation: /docs/api",
            "",
            "## Contact",
            "",
            "Email: ringzero.llc@gmail.com",
        ])
    else:
        lines.extend([
            "## Overview",
            "",
            "ClipJot is a self-hosted bookmark manager built with FastHTML/HTMX. It provides:",
            "- Web interface for managing bookmarks",
            "- REST API for programmatic access",
            "- Chrome browser extension",
            "- iOS and Android mobile apps",
            "",
            "## Authentication",
            "",
            "All API endpoints (except /api/v1/auth/invite) require authentication.",
            "Use Bearer token in Authorization header:",
            "",
            "```",
            "Authorization: Bearer YOUR_TOKEN",
            "```",
            "",
            "Tokens can be:",
            "- Session tokens (from OAuth login)",
            "- API tokens (created in Settings > API Tokens)",
            "",
            "API tokens have scopes: 'read' or 'write'.",
            "",
            "## API Endpoints",
            "",
        ])

        for section in SECTIONS:
            if section["id"] in ["overview", "errors", "rate-limits"]:
                continue

            endpoints = get_endpoints_by_section(section["id"])
            if not endpoints:
                continue

            lines.append(f"### {section['title']}")
            lines.append("")

            for ep in endpoints:
                lines.append(f"- {ep['method']} {ep['path']}")
                lines.append(f"  {ep['summary']}")
                if ep.get("scope"):
                    lines.append(f"  Scope: {ep['scope']}")
                lines.append("")

        lines.extend([
            "## Error Responses",
            "",
            "```json",
            '{"error": "Human-readable message", "code": "ERROR_CODE"}',
            "```",
            "",
            "Error codes: INVALID_TOKEN, PERMISSION_DENIED, VALIDATION_ERROR, NOT_FOUND, RATE_LIMITED, LIMIT_EXCEEDED",
            "",
            "## Rate Limits",
            "",
            "Default: 100 requests per 60 seconds per token.",
            "",
            "## Contact",
            "",
            "Email: ringzero.llc@gmail.com",
            "Website: https://clipjot.app",
        ])

    return "\n".join(lines)
