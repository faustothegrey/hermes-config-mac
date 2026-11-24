# MCP service + HTTP endpoint map

## The MCP service (`src/mcp.mjs`)

Read-only MCP **stdio** server (newline-delimited JSON-RPC 2.0 over stdin/stdout, zero external deps),
built so local clients (e.g. Hermes Agent) can query an agent-room server. Server identity:
`name: "agent-room"`, `version: "0.1.0"`. Supported protocol versions:
`2025-11-25, 2025-06-18, 2025-03-26, 2024-11-05`.

Two tools (both annotated `readOnlyHint`, `destructiveHint: false`, `idempotentHint`):

| tool | args | returns |
|---|---|---|
| `list_rooms` | `{}` | saved rooms (`~/.local/state/agent-room/rooms.json`) + rooms open on the running server, with running/active status |
| `list_discussions` | `{ "root": "<path>" }` (required) | open dated discussions (`discussions/`) + brainstorms (`brainstorms/`), excluding `archive/` and `deferred/`, with running/active status and workbench vs discussion kind |

Config via env: `AGENT_ROOM_PORT` (default **5566**), `HOME` (defaults `homedir()` for the rooms file).
`rooms.json` stores an array of realpath strings; `recordRoom()` (in `src/ui.mjs`) appends and never removes
entries even when the folder is later deleted, so stale tmp/scratch paths accumulate and are reported as
"skipped … no longer exist" at query time.

### Probe it directly (no Hermes restart needed)

```bash
printf '%s\n' \
  '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-11-25","capabilities":{},"clientInfo":{"name":"probe","version":"1.0"}}}' \
  '{"jsonrpc":"2.0","method":"notifications/initialized"}' \
  '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' \
  '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"list_rooms","arguments":{}}}' \
  | node src/mcp.mjs
```

Every message is one JSON line; notifications carry no `id` and must produce **no** response.

### Wire into Hermes Agent

Add to `~/.hermes/config.yaml`:

```yaml
mcp_servers:
  agent-room:
    command: "node"
    args: ["/Users/fausto/Software/agent-room/src/mcp.mjs"]
    env: { AGENT_ROOM_PORT: "5566" }
```

MCP tools are discovered **only at Hermes startup** (no hot-reload), so this needs a restart. Stdio env is
filtered: `HOME` is in the safe baseline, but `AGENT_ROOM_PORT` must be listed explicitly in `env`.

## HTTP routing (the gotcha that bit us)

Top-level router is `route()` in `src/ui.mjs`; per-room paths go through `handleScreen()` in `src/docs.mjs`.

Top-level `route()` serves ONLY:

- `/__health` → `{ app, pid, startedAt, rooms: [ { id, root, pages } ] }` — **no `discussion` field**
- `/__room` or `/` → 302 redirect to the first room's `/r/<room>/__room`
- `/__shutdown` (POST) and `/replica/…`
- everything else → `404 "Not found: room pages are at /r/<room>/__room."`

Per-room (reachable only as `/r/<room>/…`, after `req.url` is rewritten to the sub-path):

- `/r/<room>/__room` → the screen HTML
- `/r/<room>/__health` → `{ app, pid, root, discussion: screen.room?.active ?? null, pages }` — **has `discussion`**
- `/r/<room>/__rooms` → `screen.listRooms()` (full room list) — this is where `/__rooms` lives; it is **NOT**
  served at the top level

**Pitfall (fixed in the MCP service):** fetching top-level `/__rooms` 404s. The working live-status recipe is
two steps — GET `/__health` at the top level to enumerate room `id`+`root`, then for each room GET
`/r/<id>/__health` to collect its `discussion` (active discussion). `fetchRunningRooms()` in `src/mcp.mjs`
implements exactly this, validating `app === "agent-room"` and `root` equality at each step.
