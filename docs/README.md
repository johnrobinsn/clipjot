# ClipJot Documentation

Developer documentation for the ClipJot API.

## Contents

### API Reference

- [API v1 Specification](api/v1.md) - Complete REST API documentation
- [API Changelog](api/changelog.md) - Version history and migration guides

### Examples

- [API Examples](examples/) - Sample code for common operations
  - [sync_watch.py](examples/sync_watch.py) - Python long-polling sync client

## Quick Links

| Resource | URL |
|----------|-----|
| Production API | `https://clipjot.net/api/v1` |
| Web Interface | [https://clipjot.net](https://clipjot.net) |
| API Tokens | Settings > API Tokens (after sign-in) |

## Getting Started

1. Sign in at [clipjot.net](https://clipjot.net)
2. Go to **Settings > API Tokens**
3. Create a token with desired scopes (`read` or `write`)
4. Use the token in API requests:

```bash
curl -X POST https://clipjot.net/api/v1/bookmarks/list \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}'
```

## API Overview

All endpoints:
- Use **POST** method
- Accept and return **JSON**
- Require `Authorization: Bearer TOKEN` header

### Endpoints

| Endpoint | Scope | Description |
|----------|-------|-------------|
| `/bookmarks/add` | write | Create bookmark |
| `/bookmarks/edit` | write | Update bookmark |
| `/bookmarks/delete` | write | Delete bookmark |
| `/bookmarks/list` | read | List with pagination |
| `/bookmarks/search` | read | Full-text search |
| `/bookmarks/sync` | read | Incremental sync |
| `/tags/list` | read | List all tags |
| `/tags/create` | write | Create tag |
| `/tags/update` | write | Rename tag |
| `/tags/delete` | write | Delete tag |
| `/export` | read | Export as JSON |
| `/import` | write | Import from JSON |

See [api/v1.md](api/v1.md) for complete documentation.
