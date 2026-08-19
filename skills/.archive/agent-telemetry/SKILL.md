---
name: agent-telemetry
description: "Live agent telemetry service: tails script(1) logs from Claude Code, Codex, and Antigravity TUI sessions."
version: 1.1.0
author: Hermes Agent
platforms: [macos]
---

# Agent Telemetry Service

Lightweight HTTP server on port 9900 that tails agent logs from `~/.hermes/agent-logs/<agent>/*.log` and reports which agents are active and what they're outputting.

## Endpoints

| Endpoint | Returns |
|----------|---------|
| `GET /agents` | All agents with status, latest log, tail |
| `GET /agents/<name>` | Single agent detail |

## Response shape

```json
{
  "claude": {
    "alive": true,
    "latest_log": "20260625-204512.log",
    "log_path": "/Users/fausto/.hermes/agent-logs/claude/20260625-204512.log",
    "size_bytes": 18473,
    "last_activity": "2026-06-25 20:48:12",
    "tail": "Now working on auth module...\n  ✓ test_login\n  → refactoring middleware"
  }
}
```

- `alive`: true if a log file was modified within the last 1 hour
- `tail`: last 30 lines, stripped of ANSI escape codes

## Log capture mechanism (script(1))

Shell functions in `~/.zshrc` wrap each agent CLI in a transparent `script(1)` session:

```bash
claude-tmux() {
  local logdir="$HOME/.hermes/agent-logs/claude"
  mkdir -p "$logdir"
  local logfile="$logdir/$(date +%Y%m%d-%H%M%S).log"
  script -q "$logfile" claude "$@"
}
```

`script -q` is invisible to the user — no tmux borders, no status line, no prompt change. The user sees exactly what they'd see with a bare `claude`. The raw byte stream (with ANSI codes) is written to the log file. The telemetry service strips ANSI codes on read.

### Available wrappers

- `claude-tmux` — logs to ~/.hermes/agent-logs/claude/
- `codex-tmux` — logs to ~/.hermes/agent-logs/codex/
- `agy-tmux` — logs to ~/.hermes/agent-logs/agy/

## Service management

- **Script:** `~/Software/scripts-ai/agent_telemetry.py`
- **LaunchAgent:** `com.fausto.agent-telemetry` (located at `~/Software/scripts-ai/launchagents/com.fausto.agent-telemetry.plist`)
- **Port:** 9900 (set via `AGENT_PORT` env var)
- **Logs:** `~/Software/scripts-ai/claude-usage/agent-telemetry.{out,err}.log`

Restart after code changes:
```bash
launchctl unload ~/Library/LaunchAgents/com.fausto.agent-telemetry.plist
launchctl load ~/Library/LaunchAgents/com.fausto.agent-telemetry.plist
```

## ANSI stripping

The service runs `strip_ansi()` on log tails: removes 24-bit color codes, OSC sequences, bare CRs, and collapses repeated blank lines. Raw content is preserved in the file; only the HTTP response is cleaned.

## Relationship to other services

- **Port 9899 (quota_api.py):** Claude/Codex/Antigravity quota percentages and reset times. Lightweight, polls every 10 min.
- **Port 9900 (agent_telemetry.py):** Live agent output tails. Passive reader — requires agent to be launched with a `-tmux` wrapper.
- **Port 9901 (agent_bus.py):** Agent Bus — bidirectional message broker. Read-write counterpart to telemetry. Supports stdin injection, structured messaging, human-in-the-loop. Use `*-bus` wrappers instead of `*-tmux` for active orchestration.
- **Port 8800 (hermes-live-transcript):** Web UI for the current Hermes conversation transcript. Reads `state.db` + `agent-bus-log.db`. Supports `--dev` flag for 1s polling. Auto-excludes cron sessions from session selection. See `references/hermes-live-transcript.md` for full architecture, known bugs, and restart procedure.

## Future direction

Orchestrator loop:
1. Read agent telemetry to see what agents are doing
2. Detect agents stuck at input prompt (`❯` in Claude, `>` in agy) for >2 min
3. Handle simple questions directly (config, file read, retry)
4. Escalate to human only when agent needs real feedback
