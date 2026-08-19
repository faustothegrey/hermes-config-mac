# Time Machine Backup Completion Watchdog

## Context

After resetting the Time Machine backup volume (erasing all backup history),
a full initial backup was started via `tmutil startbackup`. Since a first
full backup of ~300GB can take hours, a quiet completion monitor was needed
that alerts the user when the backup finishes — without spamming them.

## The Script

Created at `~/.hermes/scripts/tm-backup-watchdog.sh` (no_agent=True cron pattern).

| Parameter | Value |
|-----------|-------|
| Schedule | every 15 min |
| Mode | no_agent (script stdout = delivery, empty = silent) |
| State file | `~/.local/state/tm-backup-watchdog/last_phase` |
| Delivery | origin (Telegram) |

## Parsing tmutil status

`tmutil status` outputs Apple plist format, not JSON:

```
{
    BackupPhase = Starting;
    Running = 1;
    Percent = "-1";
}
```

Note the `=` signs and `;` terminators — NOT valid JSON. Extract values with grep/sed:

```bash
RUNNING=$(echo "$STATUS" | grep -E "Running = " | sed 's/.*Running = //;s/;//;s/ //g')
PHASE=$(echo "$STATUS" | grep -E "BackupPhase = " | sed 's/.*BackupPhase = //;s/;//;s/ //g')
PERCENT=$(echo "$STATUS" | grep -E "Percent = " | sed 's/.*Percent = //;s/;//;s/ //g')
```

## Phase State Machine

```
Starting → Backup (or Running) → Finishing → (Stopping) → Idle
```

The watchdog tracks the last-known phase in a state file. When it detects
a transition from a non-idle phase (Starting/Backup/Finishing) back to Idle,
it emits the completion message.

- **On first detection of Starting:** emit "Backup avviato" message
- **On Running with Percent ≥ 0:** include progress percentage
- **On Idle when previous was non-idle:** emit "Backup completato" message
- **All other cases:** silent (empty stdout)

## Status Codes

| Running | Phase | Percent | Meaning |
|---------|-------|---------|---------|
| 1 | Starting | -1 | Preparing — scanning disk |
| 1 | Backup/Running | 0-99 | Active backup with progress |
| 1 | Finishing | 100 | Cleanup phase |
| 0 | Idle | -1 | No backup in progress |

## Cron Job

```bash
cronjob(action='create', schedule='every 15m', no_agent=True,
        script='tm-backup-watchdog.sh', name='tm-backup-progress')
```

## Interaction with Other Watchdogs

The TM progress watchdog runs alongside the load watchdog (every 5m). Both
use no_agent=True. If the backup causes high CPU/load, the user receives both:

1. TM progress: "Backup in corso — fase: Backup"
2. Load alert: "Load ≥ 10 — top CPU shows backupd at XX%"

## Session Details

The script was created during the 2026-06-28 session after manually resetting
the Time Machine backup destination. The user said "verifica tra 15 min e
dammi un report" — hence the 15-min cadence.
