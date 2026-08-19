# Load Watchdog Creation — 2026-06-28

## Context

System load was critically high (21.96 1-min, 22.27 15-min) on Fausto's MacBook.
After killing Chrome, Claude, iTerm2, and restarting the Hermes gateway, load dropped
to 5.63. The user wanted a proactive alert system so future spikes are caught early
without needing a manual diagnostic session.

## The Script

Created at `~/.hermes/scripts/load-watchdog.sh` (no_agent=True cron pattern):

| Parameter | Value |
|-----------|-------|
| WARN threshold | 1-min load ≥ 10 |
| CRIT threshold | 1-min load ≥ 18 |
| Cooldown (WARN) | 15 min |
| Cooldown (CRIT) | 5 min |
| State file | `~/.hermes/cron/output/.load_watchdog_last_alert` |
| Delivery | origin (Telegram) |

### What the script checks

1. Reads 1-min / 5-min / 15-min load from `sysctl -n vm.loadavg`
2. If ≥ WARN threshold AND out of cooldown → alert with load values + top 5 CPU + gateway state
3. If ≥ CRIT threshold AND ≥ 5 min since last alert → override cooldown, send CRIT alert
4. Otherwise → silent (empty stdout, no delivery)

### Cron job

```bash
cronjob(action='create', schedule='every 5m', no_agent=True,
        script='load-watchdog.sh', name='load-watchdog')
```

No agent, no token spend. Script stdout IS the delivery.

## Load Sequence That Day

| Time | 1-min | 5-min | 15-min | Event |
|------|-------|-------|--------|-------|
| 06:27 | 21.96 | 15.25 | 13.86 | Peak — Chrome, iTerm2, Claude, Gateway |
| 06:36 | 17.57 | 14.72 | 13.74 | Chrome killed |
| 06:37 | 14.79 | 14.25 | 13.61 | After Chrome quit |
| 06:39 | 9.48 | 12.89 | 13.14 | Claude + iTerm2 killed |
| 06:44 | 5.63 | 11.05 | 12.43 | Gateway restarted (34%→12.9% CPU) |
| 07:07 | 5.26 | 15.05 | 22.27 | Recovery — 5-min/15-min still decaying |

## Related Watchdogs

A `service-watchdog` already exists in the cron list (every 5m, no_agent, deliver='all').

## Files Created

- `~/.hermes/scripts/load-watchdog.sh` — the main watchdog script
- `~/.hermes/cron/output/.load_watchdog_last_alert` — cooldown state file (auto-created on first alert)
- Also: a fixed version of `~/Backups/hermes-config/scripts/generate-backup.py` with Obsidian vault PermissionError handling
