# LinkJot API Documentation

## Overview

The LinkJot API provides programmatic access to manage your bookmarks and tags. All endpoints use JSON for request and response bodies.

**Base URL:** `https://your-domain.com/api/v1`

## Authentication

All API endpoints require authentication using a Bearer token.

### Getting an API Token

1. Log into LinkJot web UI
2. Go to **Settings → API Tokens**
3. Click **+ New Token**
4. Choose a name, scope (`read` or `write`), and expiration
5. Copy the token immediately (it won't be shown again)

### Using the Token

Include the token in the `Authorization` header:

```bash
curl -X POST https://your-domain.com/api/v1/bookmarks/list \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{}'
```

### Token Scopes

| Scope | Permissions |
|-------|-------------|
| `read` | List, search, and export bookmarks and tags |
| `write` | All read permissions plus create, edit, delete, and import |

## Rate Limiting

- **Limit:** 100 requests per 60 seconds per token
- **Response:** 429 status with `Retry-After` header when exceeded

## Error Responses

All errors return JSON with this format:

```json
{
  "error": "Human-readable message",
  "code": "ERROR_CODE"
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INVALID_TOKEN` | 401 | Missing, invalid, or expired token |
| `PERMISSION_DENIED` | 403 | Token lacks required scope |
| `VALIDATION_ERROR` | 400 | Invalid input or missing required fields |
| `NOT_FOUND` | 404 | Resource doesn't exist |
| `RATE_LIMITED` | 429 | Too many requests |
| `LIMIT_EXCEEDED` | 403 | Bookmark or tag limit reached |

---

## Bookmark Endpoints

### Add Bookmark

Create a new bookmark.

**Endpoint:** `POST /api/v1/bookmarks/add`
**Scope:** `write`

**Request:**
```json
{
  "url": "https://example.com",
  "title": "Example Site",
  "comment": "A useful resource",
  "tags": ["work", "reference"],
  "client_name": "my-app"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `url` | string | Yes | The bookmark URL |
| `title` | string | No | Display title |
| `comment` | string | No | Personal note |
| `tags` | string[] | No | Tag names (auto-created if new) |
| `client_name` | string | No | Your app name (default: "api") |

**Response (201):**
```json
{
  "id": 123,
  "url": "https://example.com",
  "title": "Example Site",
  "comment": "A useful resource",
  "tags": [
    {"id": 1, "name": "work"},
    {"id": 2, "name": "reference"}
  ],
  "client_name": "my-app",
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Example:**
```bash
curl -X POST https://your-domain.com/api/v1/bookmarks/add \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "title": "Example Site",
    "tags": ["work"]
  }'
```

---

### Edit Bookmark

Update an existing bookmark.

**Endpoint:** `POST /api/v1/bookmarks/edit`
**Scope:** `write`

**Request:**
```json
{
  "id": 123,
  "title": "Updated Title",
  "comment": "Updated note",
  "tags": ["work", "important"]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | integer | Yes | Bookmark ID |
| `title` | string | No | New title |
| `comment` | string | No | New comment |
| `tags` | string[] | No | Replace all tags |

**Response (200):** Same format as Add Bookmark, includes `updated_at`.

**Example:**
```bash
curl -X POST https://your-domain.com/api/v1/bookmarks/edit \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "id": 123,
    "title": "New Title",
    "tags": ["archived"]
  }'
```

---

### Delete Bookmark

Delete a bookmark.

**Endpoint:** `POST /api/v1/bookmarks/delete`
**Scope:** `write`

**Request:**
```json
{
  "id": 123
}
```

**Response (200):**
```json
{
  "deleted": true
}
```

**Example:**
```bash
curl -X POST https://your-domain.com/api/v1/bookmarks/delete \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"id": 123}'
```

---

### Search Bookmarks

Search bookmarks with optional filters.

**Endpoint:** `POST /api/v1/bookmarks/search`
**Scope:** `read`

**Request:**
```json
{
  "query": "python",
  "tags": ["programming"],
  "page": 1,
  "per_page": 50
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `query` | string | No | Search in title, URL, comment |
| `tags` | string[] | No | Filter by tag names (OR logic) |
| `page` | integer | No | Page number (default: 1) |
| `per_page` | integer | No | Results per page (default: 50, max: 100) |

**Response (200):**
```json
{
  "bookmarks": [...],
  "total": 150,
  "page": 1,
  "per_page": 50,
  "has_more": true
}
```

**Example:**
```bash
curl -X POST https://your-domain.com/api/v1/bookmarks/search \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "python", "per_page": 20}'
```

---

### List Bookmarks

List all bookmarks with cursor-based pagination.

**Endpoint:** `POST /api/v1/bookmarks/list`
**Scope:** `read`

**Request:**
```json
{
  "cursor": null,
  "limit": 100
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `cursor` | string | No | Pagination cursor from previous response |
| `limit` | integer | No | Results per page (default: 100, max: 500) |

**Response (200):**
```json
{
  "bookmarks": [...],
  "has_more": true,
  "next_cursor": "MTAw"
}
```

**Example:**
```bash
# First page
curl -X POST https://your-domain.com/api/v1/bookmarks/list \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"limit": 100}'

# Next page
curl -X POST https://your-domain.com/api/v1/bookmarks/list \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"cursor": "MTAw", "limit": 100}'
```

---

## Tag Endpoints

### List Tags

Get all tags with bookmark counts.

**Endpoint:** `POST /api/v1/tags/list`
**Scope:** `read`

**Request:**
```json
{}
```

**Response (200):**
```json
{
  "tags": [
    {"id": 1, "name": "work", "bookmark_count": 42},
    {"id": 2, "name": "reference", "bookmark_count": 15}
  ]
}
```

**Example:**
```bash
curl -X POST https://your-domain.com/api/v1/tags/list \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{}'
```

---

### Create Tag

Create a new tag.

**Endpoint:** `POST /api/v1/tags/create`
**Scope:** `write`

**Request:**
```json
{
  "name": "important"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Tag name (must be unique) |

**Response (201):**
```json
{
  "id": 5,
  "name": "important",
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Example:**
```bash
curl -X POST https://your-domain.com/api/v1/tags/create \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"name": "important"}'
```

---

### Update Tag

Update a tag's name.

**Endpoint:** `POST /api/v1/tags/update`
**Scope:** `write`

**Request:**
```json
{
  "id": 5,
  "name": "urgent"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | integer | Yes | Tag ID |
| `name` | string | No | New tag name |

**Response (200):** Same format as Create Tag.

**Example:**
```bash
curl -X POST https://your-domain.com/api/v1/tags/update \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"id": 5, "name": "urgent"}'
```

---

### Delete Tag

Delete a tag (removes from all bookmarks).

**Endpoint:** `POST /api/v1/tags/delete`
**Scope:** `write`

**Request:**
```json
{
  "id": 5
}
```

**Response (200):**
```json
{
  "deleted": true
}
```

**Example:**
```bash
curl -X POST https://your-domain.com/api/v1/tags/delete \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"id": 5}'
```

---

## Export & Import

### Export Bookmarks

Export all bookmarks as JSON.

**Endpoint:** `POST /api/v1/export`
**Scope:** `read`

**Request:**
```json
{}
```

**Response (200):**
```json
{
  "bookmarks": [
    {
      "url": "https://example.com",
      "title": "Example",
      "comment": "Notes here",
      "tags": ["work", "reference"],
      "client_name": "web",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "exported_at": "2024-01-20T15:00:00Z",
  "count": 150
}
```

**Example:**
```bash
curl -X POST https://your-domain.com/api/v1/export \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{}' > bookmarks.json
```

---

### Import Bookmarks

Import bookmarks from JSON (compatible with export format).

**Endpoint:** `POST /api/v1/import`
**Scope:** `write`

**Request:**
```json
{
  "bookmarks": [
    {
      "url": "https://example.com",
      "title": "Example",
      "comment": "Notes",
      "tags": ["work"]
    }
  ],
  "mode": "merge"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `bookmarks` | array | Yes | List of bookmark objects |
| `mode` | string | No | `"merge"` (default) or `"replace"` |

**Modes:**
- `merge` - Add new bookmarks, skip duplicates by URL
- `replace` - Delete all existing bookmarks first, then import

**Response (201):**
```json
{
  "imported": 45,
  "skipped": 5,
  "errors": null
}
```

**Example:**
```bash
# Import from previously exported file
curl -X POST https://your-domain.com/api/v1/import \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d @bookmarks.json

# Or with inline data
curl -X POST https://your-domain.com/api/v1/import \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "bookmarks": [
      {"url": "https://example.com", "title": "Example"}
    ],
    "mode": "merge"
  }'
```

---

## Quick Reference

| Endpoint | Method | Scope | Description |
|----------|--------|-------|-------------|
| `/api/v1/bookmarks/add` | POST | write | Create bookmark |
| `/api/v1/bookmarks/edit` | POST | write | Update bookmark |
| `/api/v1/bookmarks/delete` | POST | write | Delete bookmark |
| `/api/v1/bookmarks/search` | POST | read | Search bookmarks |
| `/api/v1/bookmarks/list` | POST | read | List all bookmarks |
| `/api/v1/tags/list` | POST | read | List all tags |
| `/api/v1/tags/create` | POST | write | Create tag |
| `/api/v1/tags/update` | POST | write | Update tag |
| `/api/v1/tags/delete` | POST | write | Delete tag |
| `/api/v1/export` | POST | read | Export all bookmarks |
| `/api/v1/import` | POST | write | Import bookmarks |
