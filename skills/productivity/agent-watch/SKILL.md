---
name: agent-watch
description: Watch an agent tmux session in the background and notify on completion
version: 1.0.0
---

# Agent Watch — heartbeat safety net

After sending a baton to an agent and waiting for output, update the heartbeat timestamp so I get woken up if I go quiet for 5+ minutes.

## Mechanism

A cron job (`hermes-heartbeat`, every 1m, no_agent=True) runs `~/.hermes/scripts/heartbeat.sh` which checks a timestamp file. If stale >5min and not yet notified, it delivers a warning to all connected channels (conversation + Telegram) — waking me up.

## The timestamp file

At the END of every response during an active session where I'm waiting on agents:

```bash
date +%s > ~/.hermes/heartbeat/last-response
```

## Cron job config

| Field | Value |
|---|---|
| Name | hermes-heartbeat |
| Schedule | every 1m |
| no_agent | true (bash script, no LLM cost) |
| Script | heartbeat.sh |
| Deliver | all (fans out to conversation + all home channels including Telegram) |

## Rules

1. Update timestamp at end of every response when waiting on agents.
2. Cron runs every 1 minute — only fires once per stale period (`.notified` flag prevents spam).
3. When timestamp gets updated (by a new response), `.notified` is auto-cleared on next cron check.
4. No agent interference — purely checks my own activity timestamp.

## Related files

| File | What it contains |
|---|---|
| `references/heartbeat-details.md` | Implementation detail: files, cron config, anti-spam, limitations |
| `~/.hermes/scripts/heartbeat.sh` | The bash script that checks staleness |
| `~/.hermes/heartbeat/last-response` | Timestamp file (written by SM at end of response) |
| `~/.hermes/heartbeat/.notified` | Anti-spam marker (auto-cleared on fresh timestamp) |
