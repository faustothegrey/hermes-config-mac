# Quota-Monitoring Transient Processes (codex, agy, claude)

## Observation

Short-lived agent processes spawned by the local quota-monitoring proxy (`~/Software/scripts-ai/quota-monitoring/`). These appear in three varieties, each in a tmux session named `ai_cli_quotas_*`:

| Session pattern | Agent | Duration |
|----------------|-------|----------|
| `ai_cli_quotas_codex_{pid}_{ts}` | codex | ~35s |
| `ai_cli_quotas_agy_{pid}_{ts}` | agy | ~35s |
| `ai_cli_quotas_claude_{pid}_{ts}` | claude | ~35s |

## Signature

### codex
```
PID    PPID  STATE  %CPU  CWD                          COMMAND
72968 72967  R+      0.4  /private/tmp/codex-quota-*    /.../codex (binary)
72967 65301  Ss+     0.0  /private/tmp/codex-quota-*    node /usr/local/bin/codex
```

### agy / claude
Similar pattern — comm matches `agy` or `claude`, CWD is a temp dir, tmux session name starts with `ai_cli_quotas_`.

Key indicators:
- **Session name:** `ai_cli_quotas_<agent>_<pid>_<ts>` (consistent prefix)
- **Working directory:** `/private/tmp/<agent>-quota-<random>/` (temp dir cleaned up)
- **Duration:** ~35s, then self-terminates
- **CPU:** Low (< 1%)
- **Parent infrastructure:** The quota-monitoring API server (`api.py` listening on port 9899)

## Root cause

The quota-monitoring system (`~/Software/scripts-ai/quota-monitoring/api.py`) periodically spawns agent instances to measure quota consumption. These are not user-launched sessions — they are automated probes that create a throwaway tmux session, scrape `/usage` or `/status`, and kill it.

## How `agentctl health` handles them (since 2026-07-04)

`agentctl health --json` (in `check_all_agents()`) now explicitly detects quota-monitoring transient sessions:

```python
# In check_all_agents(), after building known_pids:
quota_pids = set()
for sess_name in tmux list-sessions:
    if sess_name.startswith("ai_cli_quotas_"):
        pane_pids = tmux list-panes -t sess_name
        quota_pids.update(pane_pids + their descendants)

# Then filter from process list:
procs = [p for p in find_processes(agent) if p["pid"] not in quota_pids]
```

The processes are excluded from count, orphan detection, and anomaly reporting before any JSON/human output is produced. They never reach the `agent-minder` cron job.

## How to confirm

```bash
# 1. Check if the quota monitoring API is running
ps aux | grep quota-monitoring | grep -v grep
# → Python /Users/fausto/Software/scripts-ai/quota-monitoring/api.py

# 2. List active quota-transient tmux sessions
TMUX_TMPDIR=/tmp tmux list-sessions -F "#{session_name}" | grep ai_cli_quotas_

# 3. Check their pane PIDs
TMUX_TMPDIR=/tmp tmux list-panes -t ai_cli_quotas_codex_* -F "#{pane_pid}"

# 4. Verify they DON'T appear in health output
agentctl health --json | python3 -m json.tool
# → process count for each agent should be 0 for quota transients
```

## Severity

🟢 Negligible — self-resolving within ~35s. The processes use minimal resources and clean up after themselves. **No longer cause false positives in `agentctl health` since the 2026-07-04 filter was added.**
