# Hermes Live Transcript — launchd service

**Label:** `com.fausto.hermes-live-transcript`
**Setup date:** 28 June 2026
**Last updated:** 28 June 2026 — agent bar source changed from dead Agent Bus (9901) to Agent Telemetry (9900)

## Service details

| Field | Value |
|---|---|
| Port | 8800 |
| URL | `http://127.0.0.1:8800` |
| Source | `~/Software/scripts-ai/hermes-live-transcript/server.py` |
| Python | `/usr/local/bin/python3` (Homebrew, not system Python) |
| Launchd PID ref | `launchctl list com.fausto.hermes-live-transcript` |
| Log | `~/.hermes/logs/live-transcript.log` |

This service uses `/usr/local/bin/python3` (Homebrew) in its plist, NOT `/usr/bin/python3`. This was intentional: the hermes-live-transcript server imports from the Hermes session DB (`state.db`), and the Homebrew Python's `sys.path` includes more packages. If relocated to `/usr/bin/python3`, add `sys.path.insert(0, ...)` for all Hermes lib directories before imports (see the "Launchd Python import path" pitfall in the main SKILL.md).

## REST endpoints

| Endpoint | Description |
|---|---|
| `GET /` | HTML transcript UI (single-page, dark theme) |
| `GET /api/current` | Current session messages (supports `?after=N&bus_after=M&limit=N`) |
| `GET /api/status` | Current session ID |
| `GET /api/bus/status` | Agent liveness from Agent Telemetry (port 9900) — replaces the deprecated Agent Bus (port 9901) |

### Agent bar data flow

```
agent-telemetry:9900/agents  →  transcript:8800/api/bus/status  →  JS agent-bar polling
```

The agent bar on the transcript UI polls `/api/bus/status` every 5 seconds. That endpoint in turn fetches from `http://127.0.0.1:9900/agents` (the agent-telemetry service), formats the response with type labels (agy→gemini), and filters out test agents (agenttest, smtest).

**Historical note:** The original implementation fetched from the Agent Bus HTTP server on port 9901. That server was deprecated (see `~/Software/scripts-ai/agent-bus/DEPRECATED.md`) — agentctl now talks directly to agents via tmux with no intermediary broker. The transcript UI was updated on 28 June 2026 to use agent-telemetry instead.

## Agent type mapping (client-side)

The frontend applies consistent colors and labels:

| Source name | Display name | CSS color |
|---|---|---|
| `agy` | `gemini` | `var(--gemini)` (green) |
| `claude` | `claude` | `var(--claude)` (purple) |
| `codex` | `codex` | `var(--codex)` (blue) |

## Plist

Canonical plist: `~/Software/scripts-ai/hermes-live-transcript/com.fausto.hermes-live-transcript.plist`
Deployed to: `~/Library/LaunchAgents/com.fausto.hermes-live-transcript.plist`

The plist is version-controlled inside the project repo (same pattern as agent-telemetry and agent-bus). After modifying, copy to LaunchAgents and reload:

```bash
cp ~/Software/scripts-ai/hermes-live-transcript/com.fausto.hermes-live-transcript.plist \
  ~/Library/LaunchAgents/com.fausto.hermes-live-transcript.plist
```

## Related services

The separate `agent-telemetry` service (port 9900, PID 815, label `com.fausto.claude-api` — yes, it predates the rename) provides a JSON-only `/agents` endpoint that tails agent log files. The live transcript UI (port 8800) reads from the Hermes session DB for messages and from agent-telemetry for agent liveness.

## Restart

```bash
kill $(lsof -ti :8800)  # launchd KeepAlive restarts automatically
# or explicit:
launchctl kickstart -kp gui/$(id -u)/com.fausto.hermes-live-transcript
```

## Verification

```bash
curl -s http://127.0.0.1:8800/api/bus/status | python3 -m json.tool
# Expected: {"agents": [{"name": "agy", "type": "gemini", "alive": true}, ...]}
```
