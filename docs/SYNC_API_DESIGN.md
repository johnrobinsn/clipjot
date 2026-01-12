# Design Discussion: Transactional Sync API

## Current System Overview

**Bookmark Table:**
- `id`: Auto-increment INTEGER (SQLite)
- `created_at`, `updated_at`: ISO 8601 timestamp strings
- Index exists: `idx_bookmark_user_created ON bookmark(user_id, created_at DESC)`

**Current Pagination:** Offset-based with base64-encoded cursor (just encodes offset number)

---

## Proposed Feature: Transactional Sync API

Allow external systems to:
1. Sync all existing bookmarks incrementally
2. "Tail" new bookmarks as they arrive
3. Resume after arbitrarily long gaps
4. Support multiple independent consumers per user

---

## Design Options

### Option A: Use Auto-Increment ID as Cursor

**How it works:**
- Cursor = last seen bookmark ID
- Query: `WHERE user_id = ? AND id > ? ORDER BY id ASC`
- New bookmarks always have higher IDs

**Pros:**
- Simple to implement
- IDs are guaranteed monotonically increasing
- No schema changes needed
- Efficient with index on `(user_id, id)`

**Cons:**
- Doesn't capture updates/edits (only new records)
- Doesn't capture deletes
- ID gaps may confuse clients (though not functionally problematic)

### Option B: Use created_at Timestamp as Cursor

**How it works:**
- Cursor = ISO timestamp of last seen bookmark
- Query: `WHERE user_id = ? AND created_at > ? ORDER BY created_at ASC`

**Pros:**
- Human-readable cursors
- Already indexed

**Cons:**
- Timestamp precision issues (two bookmarks same millisecond)
- Doesn't capture updates or deletes
- Slightly more complex cursor encoding

### Option C: Add Sequence Number Column

**How it works:**
- Add `seq_num` column: global or per-user monotonic sequence
- Cursor = last seen sequence number
- Increment on every INSERT

**Pros:**
- Clean abstraction
- Could extend to track updates (bump seq on UPDATE)

**Cons:**
- Schema migration required
- More complexity
- Still doesn't handle deletes naturally

### Option D: Event Log / Change Data Capture (CDC)

**How it works:**
- New table: `bookmark_events(id, user_id, bookmark_id, event_type, timestamp, data)`
- Event types: `created`, `updated`, `deleted`
- Cursor = last event ID

**Pros:**
- Full change history (creates, updates, deletes)
- Clean separation of concerns
- Multiple consumers can track independently
- Supports "replay" from any point

**Cons:**
- Most complex to implement
- Storage overhead (events accumulate)
- Need to manage event retention/cleanup
- Requires triggers or application-level hooks

---

## Key Complications

### 1. Updates and Deletes
- **Problem:** Your use case mentions syncing links, but what if a link is edited (title changed, tags modified) or deleted?
- **Question:** Should consumers see updates/deletes, or only new creations?

### 2. Consistency During Pagination
- **Problem:** While paginating through results, new bookmarks may be added
- With ID-based cursor: New items appear at end (safe)
- With timestamp cursor: Potential for missed items if clock skew

### 3. Cursor Validity
- **Problem:** What if a cursor references a deleted bookmark?
- **Solution:** Use `>=` instead of `>` with deduplication, or validate cursor

### 4. Multiple Consumers
- **Problem:** Each consumer needs independent cursor tracking
- **Options:**
  - Client-managed: Client stores their cursor (simpler)
  - Server-managed: Store cursor per (user, consumer_id) (more complex)

### 5. Rate Limiting / Polling Frequency
- **Problem:** Consumers polling aggressively could overload system
- **Solution:** Rate limits already exist (100 req/60s), may need adjustment

### 6. Large Backlogs
- **Problem:** New consumer starting from null needs to sync 1000+ bookmarks
- **Solution:** Pagination with reasonable page size (50-100)

### 7. Retention / Compaction
- If using event log: How long to keep events?
- If consumer hasn't synced in 1 year, can they still resume?

---

## Open Questions

1. **Scope of changes:** Do you need to track only NEW bookmarks, or also UPDATES and DELETES?

2. **Cursor management:** Should the server track cursors per consumer, or should clients manage their own cursor state?

3. **Real-time vs polling:** Is polling sufficient, or would you eventually want webhooks/push notifications?

4. **Data included:** Should sync responses include full bookmark data (with tags), or minimal data with option to fetch details?

5. **Authentication:** Should this use existing API tokens, or a separate sync-specific auth?

---

## Recommended Approach (Pending Answers)

For a simple "tail new bookmarks" use case, **Option A (ID-based cursor)** is likely sufficient:

```
POST /api/v1/bookmarks/sync
{
  "cursor": null,        // or last seen ID as string
  "limit": 50
}

Response:
{
  "bookmarks": [...],
  "cursor": "12345",     // ID of last bookmark in this batch
  "has_more": true
}
```

If you need update/delete tracking, **Option D (Event Log)** is more robust but significantly more work.

---

## Example Use Cases

1. **LLM Auto-tagger**: Polls for new bookmarks, fetches content, uses LLM to generate tags/summaries, updates bookmark via API
2. **Backup Service**: Periodically syncs all bookmarks to external storage
3. **Search Indexer**: Maintains full-text search index of bookmark content
4. **Analytics Dashboard**: Tracks bookmark patterns over time
