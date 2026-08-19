# Heartbeat Implementation Detail

## Files

| File | Purpose |
|---|---|
| `~/.hermes/scripts/heartbeat.sh` | bash script: checks timestamp staleness, fires once per stale period |
| `~/.hermes/heartbeat/last-response` | timestamp written at end of every SM response during active sessions |
| `~/.hermes/heartbeat/.notified` | marker file — prevents duplicate notifications per stale period |

## Cron job

Name: `hermes-heartbeat`
Schedule: `every 1m`
Script: `heartbeat.sh`
Delivery: `all` (fans out to all connected channels including this conversation)

## How it works

1. SM writes current `date +%s` to `last-response` at end of every response.
2. Cron fires every 1 minute, runs heartbeat.sh.
3. Script checks if `last-response` is >300 seconds old. If fresh, clears `.notified` and exits silently.
4. If stale AND `.notified` doesn't exist yet, creates `.notified` and echoes a warning.
5. The echo output is delivered by the cron system to `all` connected channels.
6. Once SM responds again (writing fresh timestamp), the next cron check clears `.notified`.

## Anti-spam

The `.notified` flag ensures exactly ONE notification per stuck period, no matter how long the agent stays stuck. When the SM eventually responds, the fresh timestamp + cron clear clears the flag for next time.

## Limitations

- Delivery to Telegram requires Telegram to be wired as a home channel — if not, `all` won't reach it.
- The cron runs every 1 minute but the staleness threshold is 5 minutes, so the first notification fires ~6 min after the last response at worst.
