# Service Watchdog — Configuration and Session Notes

## Service Map (Fausto's macOS)

All services managed via `~/Library/LaunchAgents/com.fausto.*.plist`, source in `~/Software/scripts-ai/`.

| Service | label | Port | Script | Log |
|---------|-------|------|--------|-----|
| agent-bus | `com.fausto.agent-bus` | 9901 | `~/Software/scripts-ai/agent-bus/server.py` | `~/.hermes/logs/agent-bus.log` |
| quota-api | `com.fausto.claude-api` | 9899 | `~/Software/scripts-ai/quota-monitoring/api.py` | `~/.hermes/logs/claude-api.log` |
| agent-telemetry | `com.fausto.agent-telemetry` | 9900 | `~/Software/scripts-ai/agent-telemetry/server.py` | `~/.hermes/logs/agent-telemetry.log` |
| claude-usage | `com.fausto.claude-usage` | 8080 | `~/Software/scripts-ai/claude-usage/cli.py scan` | `~/.hermes/logs/claude-usage.log` |

All serve over HTTP on localhost only (127.0.0.1).

## Watchdog Scheduler

- **Script:** `~/.hermes/scripts/service-watchdog`
- **Cron job:** `service-watchdog` (every 5m, no_agent=True)
- **State file:** `~/.hermes/service-monitor-state.json`
- **Flag file:** `~/.hermes/.watchdog-no-restart` (create to disable auto-restart)

## Flag File Mechanism

Created 2026-06-28 after resolving a high-load event (load peaked at 21.96). 
The user wanted alerts but no automatic restarts while the system stabilised.

**To re-enable:** `rm ~/.hermes/.watchdog-no-restart`
**To disable again:** `touch ~/.hermes/.watchdog-no-restart`

The watchdog checks for this file on every run. When present, it notes the DOWN
state and sends the alert (Telegram + email) but skips all restart attempts.

## Restart Commands

```bash
# Primary — kill and restart in one shot
launchctl kickstart -kp gui/$(id -u)/com.fausto.agent-bus

# Fallback — bootout + bootstrap
launchctl bootout gui/$(id -u)/com.fausto.agent-bus 2>/dev/null
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.fausto.agent-bus.plist
```

## Safety Thresholds

| Check | Source | Threshold |
|-------|--------|-----------|
| Load | `sysctl -n vm.loadavg` (field 2) | ≥ 10 → skip restart |
| Disk free | `os.statvfs("/")` f_bavail × f_frsize | < 5 GB → skip restart |
| Memory pressure | `vm_stat` page-ins / page-outs ratio | > 10:1 → skip restart |
| Max restart attempts | State file counter | 3 per service, resets after 1h uptime |

## Script Architecture

The watchdog is Python (not bash) because it tracks complex state (JSON),
sends email via SMTP, and performs multiple health checks per run.

Key design decisions:
- `no_agent=True` — zero LLM token cost on every 5-min check
- Silent when healthy — empty stdout = no output = no Telegram delivery
- Early exit on safety violations — checks system health BEFORE attempting any restart
- Counter resets only after 1h uptime — prevents rapid restart->fail->restart->fail cycles
- Periodic re-alert — if a service remains down past max attempts, re-alerts every 30 min
