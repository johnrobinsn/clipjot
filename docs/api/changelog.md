# API Changelog

Version history and migration guides for the ClipJot API.

---

## v1 (Current)

**Released:** January 2025

Initial API release with full bookmark and tag management capabilities.

### Features

- **Bookmarks**
  - Create, read, update, delete operations
  - Full-text search across URL, title, and comment
  - Tag filtering
  - Pagination (cursor-based and page-based)
  - Incremental sync with long polling

- **Tags**
  - Create, rename, delete tags
  - Automatic tag creation when adding bookmarks
  - Tag usage counts

- **Authentication**
  - Bearer token authentication
  - OAuth session tokens
  - API tokens with scopes (read/write)
  - Invite code authentication

- **Data Management**
  - JSON export
  - JSON import with merge/replace modes

- **Rate Limiting**
  - 100 requests per 60 seconds per token

### Endpoints

| Endpoint | Method | Scope |
|----------|--------|-------|
| /api/v1/auth/invite | POST | public |
| /api/v1/logout | POST | read |
| /api/v1/bookmarks/add | POST | write |
| /api/v1/bookmarks/edit | POST | write |
| /api/v1/bookmarks/delete | POST | write |
| /api/v1/bookmarks/search | POST | read |
| /api/v1/bookmarks/list | POST | read |
| /api/v1/bookmarks/sync | POST | read |
| /api/v1/tags/list | POST | read |
| /api/v1/tags/create | POST | write |
| /api/v1/tags/update | POST | write |
| /api/v1/tags/delete | POST | write |
| /api/v1/export | POST | read |
| /api/v1/import | POST | write |

---

## Future Versions

Future API versions will be documented here with migration guides when released.
