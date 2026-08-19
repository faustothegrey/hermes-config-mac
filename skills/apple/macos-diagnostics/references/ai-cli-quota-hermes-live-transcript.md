# Hermes Live Transcript (port 8800)

Web UI that displays the current Hermes conversation in real-time by reading from
`~/.hermes/state.db` (the SQLite session store) and `~/.hermes/agent-bus-log.db`
(agent-to-agent bus messages).

## Quick reference

| Property | Value |
|----------|-------|
| URL | `http://127.0.0.1:8800` |
| Script | `~/Software/scripts-ai/hermes-live-transcript/server.py` |
| LaunchAgent | `com.fausto.hermes-live-transcript` |
| Plist | `~/Library/LaunchAgents/com.fausto.hermes-live-transcript.plist` |
| Log | `~/.hermes/logs/live-transcript.log` |
| DB backend | `~/.hermes/state.db` + `~/.hermes/agent-bus-log.db` |

## Architecture

A single-file Python HTTPServer that:

1. **Auto-detects** the most recent non-cron Hermes session started today (`sessions.started_at >= midnight UTC`, excludes `cron_%` session IDs)
2. **Polls** `state.db` for transcript messages (`role NOT IN ('tool', 'session_meta')`, excludes empty-content assistant messages)
3. **Merges** with agent-bus messages from `agent-bus-log.db`, interleaved by timestamp
4. **Serves** a dark-themed HTML page that polls `/api/current` every ~seconds (3s normal, 1s in --dev mode)

### API Endpoints

| Endpoint | Params | Returns |
|----------|--------|---------|
| `GET /` | — | HTML page |
| `GET /api/current` | `limit` (60), `after` (0), `bus_after` (0), `session_id` | Messages JSON |
| `GET /api/status` | — | `{session_id, ok}` |
| `GET /api/bus/status` | — | Agent liveness from port 9900 |

## Ordering & Layout

- Messages are **oldest-first** in the API response
- The HTML page uses `flex-direction: column-reverse` so newest appears at top
- Bus messages get negative `id` values so they don't collide with transcript IDs
- 60-message cap (configurable via `?limit=`)
- Long messages (>500 chars) show `... (click to expand)` collapse

## Dev mode (`--dev`)

| Feature | Normal | `--dev` |
|---------|--------|---------|
| Poll interval | 3 seconds | 1 second |
| Browser console | silent | `[Hermes Live] DEV MODE — poll interval 1000ms` |

Pass `--dev` as a CLI arg after the port number:
```bash
python3 ~/Software/scripts-ai/hermes-live-transcript/server.py 8800 --dev
```

The poll interval is injected into the HTML via a `__POLL_INTERVAL__` placeholder
that gets replaced by `str(POLL_INTERVAL)` at serve time (`_serve_html()`).

Enabled permanently in the launchd plist by adding `<string>--dev</string>` to
`ProgramArguments`.

## Known bugs & fixes

### 1. Empty assistant messages (tool calls with no text)

When the Hermes assistant responds with only tool calls and no text content,
`content` is NULL/empty in the DB. The old query included these, rendering
invisible empty bubbles labeled "hermes".

**Fix:** Added `AND NOT (role = 'assistant' AND (content IS NULL OR content = ''))`
to the SQL WHERE clause in `get_messages()`.

### 2. Session ID flickering on refresh

`get_current_session_id()` was called fresh on every API poll. If a second
Hermes session started between polls (e.g. a CLI `hermes chat` for testing),
the UI jumped to the new session, clearing the transcript and showing
completely different messages.

**Fix (2 parts):**
- **Server:** `_pinned_session_id` module-level cache. Updated only on initial
  poll (`after=0`). Used for incremental polls (`after>0`).
- **Client JS:** Passes `session_id=${encodeURIComponent(sessionId)}` back on
  every incremental poll, so the server can serve the exact session.

### 3. last_transcript_id extraction after trim

On initial poll, the merged message list was capped to `limit` (60), then
`last_transcript_id` was extracted from the trimmed list. In theory, trimming
could lose the newest transcript message if bus messages pushed it past the
limit boundary.

**Fix:** Moved all cursor extraction (`last_transcript_id`, `last_bus_id`,
`last_id`) to **before** the cap/trim, operating on the full merged list.

### 4. Cron session stealing the auto-detect

Cron jobs (agent-minder, etc.) create sessions with IDs like `cron_bef...`
every ~3 minutes. These are always "more recent" than the user's conversation
session, so `get_current_session_id()` would pick a cron session instead of
the real Hermes conversation.

**Fix:** Added `AND id NOT LIKE 'cron_%'` to the session auto-detect query.
Only affects initial auto-detect — pinned polling (fix #2) is unaffected.

## Restart after changes

```bash
launchctl unload ~/Library/LaunchAgents/com.fausto.hermes-live-transcript.plist
launchctl load   ~/Library/LaunchAgents/com.fausto.hermes-live-transcript.plist
# Verify:
sleep 2 && curl -s http://127.0.0.1:8800/api/status
```

## Test commands

```bash
# Check empty assistant messages:
curl -s "http://127.0.0.1:8800/api/current?limit=200" | python3 -c "
import json, sys
data = json.load(sys.stdin)
empty = [m for m in data['messages'] if m['display']=='hermes' and not m['content'].strip()]
print(f'{len(empty)} empty hermes messages')
"

# Check session stability:
curl -s "http://127.0.0.1:8800/api/current?limit=1" | python3 -c "
import json, sys; d=json.load(sys.stdin); print(d['session_id'])
"

# Verify dev mode poll interval from HTML:
curl -s "http://127.0.0.1:8800/" | grep -o 'setInterval(poll, [0-9]*)'
```
