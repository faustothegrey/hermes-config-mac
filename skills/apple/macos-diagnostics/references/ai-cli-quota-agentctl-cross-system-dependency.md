# Agentctl Cross-System Dependency (tmux Session Naming Convention)

## The coupling

The quota monitoring system creates **transient tmux sessions** to scrape usage data
from CLI agents. These sessions are short-lived (~35s each, every ~10min) and self-destruct.

The `agentctl health --json` (used by `agent-minder` cron) filters these sessions out
of its anomaly detection — but only **by session name pattern**.

## The naming convention (MUST stay in sync)

Each transient session name follows this template in `~/Software/scripts-ai/ai-quota-lib/ai_quota_lib/__init__.py`:

| Function | Template | File location |
|----------|----------|---------------|
| `codex_interactive_status()` | `ai_cli_quotas_codex_{os.getpid()}_{int(time.time())}` | Line ~151 |
| `antigravity_interactive_usage()` | `ai_cli_quotas_agy_{os.getpid()}_{int(time.time())}` | Line ~284 |
| `claude_interactive_usage()` | `ai_cli_quotas_claude_{os.getpid()}_{int(time.time())}` | Line ~565 |

The filter in `agentctl` (`check_all_agents()` in `~/Software/scripts-ai/agent-bus/agentctl`)
detects them with:

```python
if sess_name.startswith("ai_cli_quotas_"):
    # collect PIDs and exclude from health check
```

**If you change the session name prefix in `ai_quota_lib/__init__.py`, you MUST update
the filter in `agentctl` too.** Currently the filter lives at ~line 138 of agentctl,
in the `check_all_agents()` function.

## Why this matters

Without this filter, every time `agent-minder` runs `agentctl health --json` during
a quota scrape window (~35s every ~10min), it flags the transient processes as:
- **Orphans** (not registered in `agent-sessions.json`)
- **Duplicates** (if the real agent is also running)

This causes false-positive anomaly reports on Telegram and wasted token consumption.

## Counterpart reference

The same dependency is documented from the agentctl side in:
`agentctl/references/quota-monitoring-transients.md`

## Regeneration test

After changing session names in either repo, verify the filter works:

```bash
# 1. Start a transient session manually to simulate a quota scrape
TMUX_TMPDIR=/tmp tmux new-session -d -s "ai_cli_quotas_codex_$$_$(date +%s)"

# 2. Run health check — must NOT flag the session processes
agentctl health --json | python3 -c "
import json, sys
data = json.load(sys.stdin)
counts = {k: v['count'] for k, v in data['agents'].items()}
print(f'Agent process counts: {counts}')
print(f'Anomalies: {data[\"anomaly_count\"]}')
print(f'Expected: all 0 anomalies and 0 count for codex')
"

# 3. Cleanup
tmux kill-session -t "ai_cli_quotas_codex_$$_$(date +%s)"
```
