# Stale tmux socket investigation — 2026-07-02

**Scenario:** Cron health check (`agentctl health --json`) reported `anomaly_count: 2` — all registered agents showed `known_count: 0`, all running processes classified as orphans. Root cause: tmux server had crashed, leaving a stale socket.

## Initial health check output

```json
{
  "load": {"1m": 2.23, "5m": 4.51, "15m": 6.0},
  "agents": {
    "agy":   {"count": 1, "processes": [...], "orphan_count": 1, "known_count": 0},
    "claude":{"count": 3, "processes": [...], "orphan_count": 3, "known_count": 0},
    "codex": {"count": 2, "processes": [...], "orphan_count": 2, "known_count": 0}
  },
  "anomaly_count": 2,
  "anomalies": ["claude: DUPLICATES", "codex: DUPLICATES"]
}
```

## Investigation sequence (raw commands)

### 1. Load + process list
```bash
uptime                                          # 18:25 up 3 days, 5:41, 6 users
ps axo pid,ppid,%cpu,%mem,rss,state,lstart,comm | grep -E '(agy|claude|codex)' | grep -v grep
```

### 2. Per-PID profiling
```bash
# Base info + PPID ancestry
ps -p <PID> -o pid,ppid,%cpu,%mem,rss,state,lstart,command
lsof -p <PID> 2>/dev/null | grep cwd           # working directory
lsof -p <PID> 2>/dev/null | grep -E 'IPv4|IPv6'  # network connections
lsof -p <PID> 2>/dev/null | head -20          # file descriptors

# Full PPID chain (iterate up to login/init)
ps -p <PPID> -o pid,ppid,command               # parent
# Most chains ended in: login -fp fausto → zsh → zsh → agent
```

### 3. tmux diagnostic
```bash
# Both paths show socket file but no server
ls -la /tmp/tmux-501/default           # socket exists
ls -la /private/tmp/tmux-501/default   # same socket (symlink)
tmux list-sessions                     # "no server running" ← STALE
tmux -S /tmp/tmux-501/default list-sessions  # same result
pgrep -la tmux                         # empty → no tmux process at all
```

### 4. agent-sessions.json registry check
```bash
cat ~/.hermes/agent-sessions.json
# All 3 agents had stale PIDs + dead tmux sessions
```

### 5. Claude session file growth check
```bash
# For each claude PID, find its project slug from cwd
lsof -p <PID> 2>/dev/null | grep cwd
# Then check project session files
ls -lt ~/.claude/projects/<slug>/
stat -f%z ~/.claude/projects/<slug>/*.jsonl  # last size
stat -f%m ~/.claude/projects/<slug>/*.jsonl  # last mod time
```

### 6. agy log analysis (heartbeat pattern)
```bash
tail -30 ~/.gemini/antigravity-cli/log/cli-<timestamp>.log
# Look for:
#   - streamGenerateContent = real work
#   - fetchAvailableModels + loadCodeAssist = heartbeat
#   - "Terminal gone, shutting down" = shutdown sequence
#   - "Waiting for migrations" = stuck db migration
grep -c "streamGenerateContent" <logfile>  # count real work calls
```

### 7. Codex state check
```bash
ls -lh ~/.codex/logs_2.sqlite         # 1.1GB → approaching runaway (1.2GB threshold)
ls -l ~/.codex/state_5.sqlite         # last modified timestamp = last real action
```

## Processes found

| PID | Agent | CPU | PPID | TTY | CWD | Classification |
|-----|-------|-----|------|-----|-----|---------------|
| 11528 | agy | 18.9% | 65433 (zsh) | ttys005 | AgentTalk | Heartbeat < 10 min, not stuck |
| 68188 | claude | 1.5% | 46855 (zsh) | ttys007 | hermes-live-transcript | Idle leftover (49 min) |
| 10994 | claude | 1.3% | 45818 (zsh) | ttys004 | /Users/fausto | Idle leftover (25 min) |
| 11009 | codex | 1.9% | 11008 (node) | ttys000 | AgentTalk | Low activity, state DB live 6 min ago |
| 71480 | codex | 0.0% | IDE Helper | — | / | FALSE POSITIVE (Antigravity IDE) |
| 27469 | claude | — | — | — | — | TRANSIENT (exited) |
| 28333 | agy | — | — | ttys002 | — | TRANSIENT (exited < 30s) |

## Key patterns observed

1. **All orphans had PPID chains ending in `login -fp fausto`** — not PPID=1. They were "registry orphans" (not tracked by agentctl) on live iTerm terminals, not true orphans.

2. **The `count > 0` but `known_count == 0` with no tmux server** is the dead-giveaway for stale tmux socket. If tmux were alive with stale PIDs, `known_count` would still be 0 but `tmux list-sessions` would show sessions.

3. **Transient processes exist** — brief agent CLI invocations (PIDs 27469, 28333) that spawn, run briefly, and exit before a health check can fully profile them. Safe to ignore.

4. **Codex logs_2.sqlite at 1.1GB** is below the 1.2GB runaway threshold from the health-check protocol, but warrants monitoring.

## Recommendations from this investigation

- **Do NOT kill** processes on live terminals unless CPU > 5% or idle > 2h with no session file growth
- **Monitor agy heartbeat** — if > 15 min without `streamGenerateContent`, kill
- **Stale tmux socket** → `rm -f /tmp/tmux-501/default /private/tmp/tmux-501/default`, then respawn
- **Transient processes** → always ignore (they self-resolve)
- **IDE extension processes** → always ignore (false positive)
