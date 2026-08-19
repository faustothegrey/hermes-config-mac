# Debugging Live-Polling Web UIs with Dynamic Data Sources

## The Pattern

A web UI polls a REST endpoint every N seconds. The endpoint dynamically selects
its data source (e.g. "most recent session today"). The endpoint is stateless —
it recalculates the data source ID on EVERY call. The client keeps a `lastId`
and uses it for incremental `?after=lastId` polling.

## The Bug: Session Switching on Refresh

### Root Cause

1. **Stateless source selection.** The API recalculates `get_current_session_id()`
   on every poll. If a new session starts between polls (even a test or `hermes chat -q`),
   the API returns a different `session_id`. The client detects the mismatch and:
   - Clears the transcript
   - Resets `lastId = 0`
   - Re-fetches all messages from the new session

2. **Result:** Refreshing the browser or just waiting a few seconds shows completely
   different messages. User perceives the UI as "flickering" or "showing random data."

### Fix Pattern

**Pin the session ID on initial load.** On first poll, snapshot `session_id` from
the API response. Subsequent polls pass this pinned ID as a query parameter
(`?session_id=pinned-value`). The server uses the pinned ID instead of recalculating.
Only allow re-pinning when the user explicitly refreshes (page reload) or the
pinned session ends (e.g. expired beyond a few minutes of no activity).

```python
# Server-side fix
def _serve_current(self):
    requested_sid = self._get_param("session_id")
    if requested_sid:
        sid = requested_sid  # honor client's pinned session
    else:
        sid = get_current_session_id()  # only on initial load
```

```javascript
// Client-side fix — pin on first poll
let pinnedSessionId = null;
async function poll() {
    const url = pinnedSessionId
        ? `/api/current?session_id=${pinnedSessionId}&after=${lastId}`
        : `/api/current?limit=${MAX_VISIBLE}`;
    const data = await (await fetch(url)).json();
    if (!pinnedSessionId && data.session_id) {
        pinnedSessionId = data.session_id;  // pin it
    }
    if (data.session_id !== pinnedSessionId) {
        return;  // ignore — we're pinned to an older session
    }
    // ... process messages
}
// Full page reload (Ctrl+R/⌘R) resets all JS state, so pinnedSessionId
// is cleared and a fresh pin happens naturally.
```

## Common Variant: Empty Messages from Tool-Call-Only Assistant Turns

### Root Cause

The API filters `WHERE role NOT IN ('tool', 'session_meta')` but includes
`assistant` rows where `content IS NULL OR content = ''`. These are assistant
turns that made tool calls but had no text response. The UI renders them as
empty message bubbles.

### Fix

Add a content-non-empty filter:

```python
WHERE role NOT IN ('tool', 'session_meta')
  AND NOT (role = 'assistant' AND (content IS NULL OR content = ''))
```

Or filter server-side before returning:

```python
result = [m for m in result if not (m["role"] == "assistant" and not m["content"])]
```

## Common Variant: Timestamp-Based Merge Truncation

### Root Cause

When merging two data sources (e.g. transcript messages + agent-bus messages)
by timestamp, then capping the merged list (e.g. last 60 messages), the
`last_id` for incremental polling is extracted from the capped list. If a
transcript message was pushed outside the cap by newer bus messages, the
`last_id` retrocedes — causing the next poll to re-fetch already-seen
transcript messages and create duplicates.

### Fix

Extract `last_transcript_id` from the FULL merged list BEFORE trimming:

```python
# 1. Merge
merged = merge_by_timestamp(transcript_msgs, bus_msgs)

# 2. Extract IDs from the full list
last_transcript_id = max(m["id"] for m in merged if m.get("id", 0) > 0)

# 3. Then trim
if len(merged) > limit:
    merged = merged[-limit:]

data["messages"] = merged
data["last_transcript_id"] = last_transcript_id
```

## Common Variant: Internal/System Sessions Override User Sessions

### Root Cause

`get_current_session_id()` selects the most recently started session. If the
system creates frequent internal sessions (cron jobs, health checks,
administrative tasks), these can be "newer" than the user's current
conversation session. The auto-detection keeps switching to internal sessions
instead of the user's session.

### Fix

Filter out internal session ID patterns in the SQL query:

```python
SELECT id FROM sessions
WHERE started_at >= ?
  AND id NOT LIKE 'cron_%'   -- exclude cron jobs
ORDER BY started_at DESC LIMIT 1
```

Or expose `session_id` as a client-provided parameter so the client can pin
to a non-cron session explicitly.

## In-Conversation Blindness: Hermes DB Flush Delay

### Root Cause

During an active Hermes conversation, **state.db updates are asynchronous.**
The conversation loop writes messages to state.db incrementally:
- Tool-output messages (role `tool`) are written promptly
- Assistant text responses are written when the response completes
- Between turns, the DB has a snapshot of messages up to the LAST completed
  exchange — current-turn messages may not be in the DB yet

A live-polling UI that reads from state.db will appear to "freeze" or "stall"
during an active conversation because the DB hasn't been updated yet.

### Diagnosis

Query the DB multiple times over a 5-10 second window. If the message count
doesn't increase even though you can see new messages in your Hermes TUI,
you're seeing the flush delay:

```bash
# Quick check — run twice with a gap
sqlite3 ~/.hermes/state.db "SELECT MAX(id), COUNT(*) FROM messages
  WHERE session_id = (SELECT id FROM sessions ORDER BY started_at DESC LIMIT 1);"
sleep 4
sqlite3 ~/.hermes/state.db "SELECT MAX(id), COUNT(*) FROM messages
  WHERE session_id = (SELECT id FROM sessions ORDER BY started_at DESC LIMIT 1);"
# If both return the same MAX(id), the DB hasn't flushed yet
```

### What This Means

This is NOT a UI bug — it's an **architectural constraint** of reading from
Hermes' persistent store in real-time. The UI is not frozen: it's polling
correctly and the DB simply hasn't received new data yet. The messages will
appear once Hermes completes the current conversation turn and flushes to
state.db (typically within 1-3 seconds of the response appearing in the TUI).

### Fix Options

1. **Accept the delay.** The DB flush is naturally fast (~1-3s). The UI will
   catch up on the next poll cycle. This is the simplest and most reliable
   approach.
2. **Increase poll frequency.** Reduce from 3s to 1s for faster catch-up. Risk:
   more server load and battery drain.
3. **Read from the gateway event stream** instead of state.db if sub-second
   real-time is required. This is a much larger architectural change.

## Verification

To confirm the session-switching fix: open the live-polling UI, start a second
session in another terminal (`hermes chat -q "hello"`), and verify the UI
stays on the pinned session instead of jumping.

To confirm the empty-messages fix: check for assistant messages with no content
in the underlying DB:

```bash
sqlite3 ~/.hermes/state.db "
SELECT id, role, CASE WHEN content IS NULL THEN 'NULL' WHEN content = '' THEN 'EMPTY' ELSE 'content' END
FROM messages
WHERE role = 'assistant' AND (content IS NULL OR content = '')
  AND session_id = (SELECT id FROM sessions ORDER BY started_at DESC LIMIT 1)
ORDER BY id;"
```
