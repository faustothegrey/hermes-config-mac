# no_agent Scripting Patterns for macOS

## Why These Rules Exist

macOS shell scripts running as `no_agent=True` cron jobs have specific failure
modes that don't appear in interactive terminals or Linux environments. These
patterns were hard-earned during the 2026-06-28 session after a `load-watchdog`
script kept exiting with code 141 (SIGPIPE) and a `tm-backup-watchdog` script
also hit similar issues.

## Rule 1: No `set -euo pipefail`

**Symptom:** The script exits with code 141 (SIGPIPE = 128 + 13) at seemingly
random times.

**Root cause:** macOS `ps` receives SIGPIPE when a pipeline consumer (like
`head`) closes the pipe early. With `pipefail`, this non-zero exit propagates,
and the script dies.

Common patterns that trigger it:

```bash
# SIGPIPE time bombs:
TOP_CPU=$(ps axo pid,pcpu,comm -r | head -6 | tail -5)
GATEWAY_CPU=$(ps aux | grep "[g]ateway" | head -1)
```

**Fix:** Do NOT use `set -euo pipefail` in no_agent scripts. Handle errors
explicitly. Alternatively, consume the remaining pipe:

```bash
# Safe pattern:
TOP_CPU=$(ps axo pid,pcpu,comm -r | { head -6; cat >/dev/null; } | tail -5)
```

## Rule 2: Use `awk`, Not `bc`, for Comparisons

**Symptom:** Floating-point comparison silently returns false or the comparison
line errors.

**Root cause:** `bc` may not be in the PATH for cron subprocesses on macOS.
Even though `/usr/bin/bc` exists, the PATH filtering in cron's process
environment can make it unavailable.

**Fix:** Use `awk` for all float comparisons — it's always available:

```bash
# Comparison helper function:
ge() { awk -v a="$1" -v b="$2" 'BEGIN{exit !(a>=b)}'; }

# Usage:
if ge "$LOAD_1" "$WARN_THRESHOLD"; then
    ...
fi
```

## Rule 3: Exit 0 Always for no_agent Scripts

**The delivery contract:**
- **Empty stdout** → nothing delivered, cron logs "ok"
- **Non-empty stdout** → delivered to the target platform
- **Exit non-zero** → cron logs "error" with the exit code, even if stdout
  had valid content

Wrap all logic to ensure the script exits 0:

```bash
# Always end with:
exit 0
```

## Rule 4: Cooldown via State Files

To prevent alert spam from scripts that run every few minutes, use a
plain-text state file:

```bash
STATE_FILE="$HOME/.hermes/cron/output/.my_watchdog_cooldown"
mkdir -p "$(dirname "$STATE_FILE")"

LAST_ALERT=$(cat "$STATE_FILE" 2>/dev/null || echo "0")
NOW_EPOCH=$(date +%s)
DELTA=$(( (NOW_EPOCH - LAST_ALERT) / 60 ))

if [ "$DELTA" -ge "$COOLDOWN_MINUTES" ]; then
    echo "$NOW_EPOCH" > "$STATE_FILE"
    # emit alert...
fi
```

## Rule 5: Test Before Deploying

Run the script manually in the same environment (bash, not zsh):

```bash
bash ~/.hermes/scripts/my-watchdog.sh
echo "Exit: $?"
```

If the exit code is anything other than 0 under normal conditions, fix it
before creating the cron job.

## macOS-Specific Tool Availability

| Tool | In cron PATH? | Fallback |
|------|--------------|----------|
| `awk` | ✅ Always | — |
| `sed` | ✅ Always | — |
| `grep` | ✅ Always | — |
| `ps` | ✅ Always | — |
| `sysctl` | ✅ Always | — |
| `bc` | ⚠️ Sometimes missing | Use awk |
| `python3` | ⚠️ Sometimes missing | Use awk/sed |
| `tmux` | ❌ `/usr/local/bin/` | Use full path |
| `agy` | ❌ `~/.local/bin/` | Use full path |

## Script Template

```bash
#!/bin/bash
# watchdog-template.sh — no_agent safe script template
# Silent when healthy, emits alerts when triggered.

WARN_THRESHOLD=10
STATE_FILE="$HOME/.hermes/cron/output/.template_cooldown"
COOLDOWN_MINUTES=15

# Comparison helper — awk, not bc
ge() { awk -v a="$1" -v b="$2" 'BEGIN{exit !(a>=b)}'; }

# Read metric
VALUE=$(sysctl -n vm.loadavg 2>/dev/null | awk '{print $2}')
[ -z "$VALUE" ] && exit 0

# Cooldown check
LAST_ALERT=$(cat "$STATE_FILE" 2>/dev/null || echo "0")
NOW_EPOCH=$(date +%s)
DELTA=$(( (NOW_EPOCH - LAST_ALERT) / 60 ))

if ge "$VALUE" "$WARN_THRESHOLD" && [ "$DELTA" -ge "$COOLDOWN_MINUTES" ]; then
    echo "⚠️ Alert: value is ${VALUE}"
    mkdir -p "$(dirname "$STATE_FILE")"
    echo "$NOW_EPOCH" > "$STATE_FILE"
fi

exit 0
```
