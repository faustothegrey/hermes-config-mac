# Active Hermes config backup installations

## MacBook (fausto-mac)

| Property | Value |
|----------|-------|
| Repo | `git@github.com:faustothegrey/hermes-config-mac.git` |
| Clone | `~/Backups/hermes-config/` |
| Cron job ID | `b763d78565da` |
| Schedule | `0 23 * * *` (23:00 nightly — check with `hermes cron list`) |
| Cron entry-point | `~/.hermes/scripts/hermes-config-backup-nightly.sh` |
| Mode | no-agent (script stdout = delivery) |
| Last run | 2026-07-12 00:18 CEST — status: error |
| Total commits | 27 (as of 2026-07-12) |
| SSH key | `~/.ssh/id_rsa` |

### Diagnosis: cron job shows error

The backup script (`backup-hermes.sh`) uses `set -euo pipefail`. Even though `git commit`
succeeds, the script exits with non-zero on the next failure. Likely cause:

1. **git push fails** — intermittent SSH auth or network
2. **SSH key missing** at `~/.ssh/id_rsa.pub` — encryption step skips to stderr but
   that alone doesn't kill the script; push failure is the real culprit

To verify, run the script manually:
```
cd ~/Backups/hermes-config && bash scripts/backup-hermes.sh
```
Look for the final `git push` line. If it errors, run `ssh -T git@github.com` to
check SSH auth.

### What it backs up
- Hermes config, skills (99 skills across 16 categories), cron, profiles, plugins, memories, hooks
- Obsidian vault (Hermes Memory/ notes)
- Encrypted secrets: `.env`, `auth.json`, `gateway_state.json`, `state.db` (~47 MB)

### Scripts
- `scripts/generate-backup.py` — Python sanitized snapshot generator
- `scripts/backup-hermes.sh` — orchestration (generate → encrypt → commit → push)
- `scripts/restore-hermes.sh` — full restore with secret decryption

## peer84 (N56VV — Ubuntu 22.04)

| Property | Value |
|----------|-------|
| Repo | `git@github.com:faustothegrey/hermes-config.git` |
| Clone | `/home/fausto/Backups/hermes-config/` |
| Cron job ID | `46e2b1f4aea4` |
| Schedule | `30 0 * * *` (00:30 nightly) |
| Cron script | `/home/fausto/.hermes/scripts/hermes-config-backup-nightly.sh` |
| Mode | no-agent |
| Hermes home | `/home/fausto/.hermes/` |
| SSH key | `/home/fausto/.ssh/id_rsa` |

Same backup architecture as the MacBook.