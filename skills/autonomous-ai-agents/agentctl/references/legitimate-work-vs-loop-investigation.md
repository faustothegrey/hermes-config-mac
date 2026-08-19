# Legitimate Work vs Loop Investigation — Session Trace 2026-07-02

## Scenario

Cron job (agent-minder, 18:36 UTC) ran `agentctl health --json` and found `anomaly_count=2`:
- **claude DUPLICATES:** 2 orphans (PID 68188, 10994)
- **codex DUPLICATES:** 2 orphans (PID 71480, 11009)

Plus a non-anomaly orphan: **agy PID 11528** (1 process, orphan=true, known_count=0).

The agy process was the hardest to classify — CPU 46.6%, 244 open files, 84 `streamGenerateContent`/min. This file documents how it was classified as **legitimate work** rather than a **runaway loop** or **stuck shutdown**.

## Step-by-step investigation

### 1. Initial profile (PIDs from health JSON)

| PID | Agent | CPU | PPID | State | Started |
|-----|-------|-----|------|-------|---------|
| 11528 | agy | **46.6%** | 65433 (zsh) | S+ | 17:00 |
| 10994 | claude | 0.1% | 45818 (zsh) | S+ | 17:00 |
| 68188 | claude | 0.7% | 46855 (zsh) | S+ | 12:37 |
| 71480 | codex | 0.0% | 71306 (IDE) | S | Jun 30 |
| 11009 | codex | 0.0% | 11008 (node) | S+ | 17:00 |

### 2. PPID ancestry — ruling out true orphans

```
PID 11528 → 65433 (-zsh) → 65432 (login) → 41792 (iTermServer)
PID 68188 → 46855 (-zsh) → 46854 (login) → 41792 (iTermServer)
PID 71480 → 71306 (IDE Helper) → 71265 (Antigravity IDE Electron) → 1 (launchd)
```

None had PPID=1. All were running in live iTerm windows, not orphaned terminals. PID 71480 was an IDE extension (false positive).

### 3. agy log inspection — the critical signal

```bash
tail -200 ~/.gemini/antigravity-cli/log/cli-20260702_170055.log
```

**Found pattern from 17:00-18:10:** Only heartbeat — `fetchAvailableModels` + `loadCodeAssist` every ~5 min, no `streamGenerateContent`.

**Found at 18:10:14:**
```
HandleUserInput called with text: "reviewer found blocking issues in T2. Please read and fix"
```

This is the definitive signal. The user sent a task to agy in an iTerm window. After this:
- `streamGenerateContent` with unique ResponseIDs every 5-15s
- 84 calls in the last 3 minutes of the window
- 170 unique Trace IDs in the last 200 log lines
- No repeated ResponseIDs (confirmed with `sort | uniq -d`)

**Key insight:** `streamGenerateContent` with unique ResponseIDs = legitimate work. Heartbeat = `loadCodeAssist` / `fetchAvailableModels` without interleaved stream calls.

### 4. File operations check — no source code writes (expected for agy)

```bash
lsof -p 11528 | grep -v ".gemini" | grep -v "antigravity-cli" | grep -E '\.(ts|js|py|md)$' | head -10
# → EMPTY — no source files open
```

agy doesn't write files directly; the user reads its output from the terminal. Not writing files is normal for agy.

### 5. Open files pattern — unusual but not problematic

```bash
lsof -p 11528 | tail -n +2 | awk '{print $NF}' | awk -F. '{print $NF}' | sort | uniq -c | sort -rn | head -5
# → 244 json  (all ~/.gemini/config/projects/*.json — project configs)
# →   2 log
```

244 project config JSONs open is unusual — the agent was scanning its project registry. Combined with the `HandleUserInput` entry, this was the agent loading context to understand the project before implementing the fix.

### 6. Working directory check — AgentTalk project

```bash
lsof -p 11528 | grep cwd
# → /Users/fausto/Software/AgentTalk
```

Confirmed: the agent was working in AgentTalk, consistent with the user message about "blocking issues in T2" (Task 2 of AgentTalk's M15 milestone).

### 7. Git commit check — recent commits from other agents

```bash
cd /Users/fausto/Software/AgentTalk && git log --oneline --since="2 hours ago"
# → a329b19 docs(ledger): file M15-T2 claim
# → f406feb fix(arbiter): implement confirmation and rejection paths
# → ...
```

The git log showed recent commits, but none from PID 11528 itself (agy doesn't commit — it tells the user what to do). The commits from other agents in the same session confirmed the project was active.

### 8. CPU trend — tapering, not escalating

| Time | CPU | Signal |
|------|-----|--------|
| First check | 46.6% | Initial alarm — possible loop |
| After 3 min | 33.8% | Still high but dropping |
| After 5 min | 17.3% | Clear downtrend |
| After 10 min | 10.5% | Approaching normal |
| After 15 min | 8.9% | Tapering toward idle |

A runaway loop would maintain or escalate CPU. A process finishing work gradually releases CPU. This downtrend confirmed legitimate work completing.

## Decision tree for future investigations

```
Find process with orphan=true, high CPU
    │
    ├─ Is it agy?
    │   ├─ Check log for "HandleUserInput called with text:"
    │   │   ├─ FOUND → LEGITIMATE WORK (user message at that timestamp)
    │   │   └─ NOT FOUND → go to stream pattern check
    │   │
    │   └─ Check log stream pattern (last 200 lines):
    │       ├─ Only loadCodeAssist/fetchAvailableModels → HEARTBEAT LOOP (kill if >15min no stream)
    │       └─ streamGenerateContent with unique ResponseIDs → WORKING
    │
    ├─ Is it claude?
    │   └─ Check session .jsonl growth over 60s:
    │       ├─ Growing → LEGITIMATE WORK
    │       └─ Flat → IDLE LEFTOVER
    │
    ├─ Is it codex?
    │   ├─ Check cmdline for "app-server" → IDE EXTENSION (false positive)
    │   ├─ Check network connections (codex NEEDS network to function):
    │   │   ├─ `lsof -p <PID> | grep -c ESTABLISHED` → 0 connections means STUCK/FROZEN
    │   │   └─ 0 connections + no state DB growth = definitively hung, not just idle
    │   └─ Check state DB growth over 60s:
    │       ├─ Growing → WORKING
    │       └─ Flat → IDLE LEFTOVER or STUCK
    │
    └─ Check CPU trend: dropping → finishing work. Stable/elevated → possible loop.
```

## Commands used during investigation

```bash
# 1. Parse JSON, collect PIDs
python3 -c "import json; d=json.loads(open('/dev/stdin').read()); [print(f'{k}: {[p[\"pid\"] for p in v[\"processes\"]]}') for k,v in d['agents'].items()]"
# → agy: [11528]  claude: [10994, 68188]  codex: [71480, 11009]

# 2. Profile each PID
ps -o pid,ppid,%cpu,%mem,rss,state,lstart,command -p <PID>

# 3. PPID ancestry
ps -p <PPID> -o pid,ppid,command
# Repeat up chain to launchd(1) or iTermServer

# 4. Working directory
lsof -p <PID> | grep cwd

# 5. agy log check (the critical signal)
grep -c "HandleUserInput called with text:" ~/.gemini/antigravity-cli/log/cli-*.log

# 6. agy stream pattern check
tail -200 ~/.gemini/antigravity-cli/log/cli-*.log | grep "streamGenerateContent" | wc -l
tail -200 ~/.gemini/antigravity-cli/log/cli-*.log | grep "loadCodeAssist" | wc -l
tail -200 ~/.gemini/antigravity-cli/log/cli-*.log | grep "streamGenerateContent" | grep -o 'ResponseID: [^ ]*' | sort | uniq -d
# uniq -d empty = all unique = legitimate work

# 7. Claude session file growth
SIZE1=$(stat -f%z ~/.claude/projects/<slug>/*.jsonl)
sleep 60
SIZE2=$(stat -f%z ~/.claude/projects/<slug>/*.jsonl)
echo "Delta: $((SIZE2 - SIZE1))"  # >0 = working

# 8. Codex state DB growth
SIZE1=$(stat -f%z ~/.codex/state_5.sqlite)
sleep 60
SIZE2=$(stat -f%z ~/.codex/state_5.sqlite)
echo "Delta: $((SIZE2 - SIZE1))"  # >0 = working

# 9. CPU trend
for i in 1 2 3; do ps -o pid,%cpu,state -p <PID>; sleep 10; done
# Downward trend → finishing job. Stable/elevated → possible problem.

# 10. File modification check in project directory
find <project_dir> -newer <log_file> -type f -not -path '*/.git/*' | head -10
---

## Claude 10994 — Stuck loop (high CPU, idle connections, no session growth)

### Scenario

Cron job (agent-minder, 01:37 UTC Jul 3) ran `agentctl health --json` and found `anomaly_count=3`:
- **agy DEAD** — registered tmux session dead (stale socket)
- **claude DUPLICATES:** 2 orphans (PID 10994, 68188)
- **codex DUPLICATES:** 2 orphans (PID 71480, 11009)

PID 10994 (Claude) was the hardest — 69% CPU, 2 ESTABLISHED connections, but zero work output.

### Step-by-step investigation

#### 1. Initial profile

| Metric | Value |
|--------|-------|
| PID | 10994 |
| Agent | Claude 2.1.198 |
| PPID | 45818 (-zsh, ttys004) — live iTerm |
| CPU | 69.0% |
| MEM/RSS | 2.9% / 484MB |
| State | S+ |
| Started | Thu Jul 2 17:00 |
| Elapsed | 8h38m |
| CPU time | 20m00s |
| CWD | /Users/fausto (home, not project) |

#### 2. PPID ancestry — live iTerm, not orphaned

```
10994 (claude) → 45818 (-zsh) → 45817 (login) → 41792 (iTermServer)
```

PPID=45818 is a live zsh on ttys004. Not a true orphan (PPID ≠ 1). This is a manual iTerm launch (Pattern 4 in common-false-positives.md).

#### 3. Network connections — established but idle

```bash
lsof -p 10994 | grep -E 'IPv4|IPv6.*ESTABLISHED'
# → 2 connections:
#   50218 → 160.79.104.10:https
#   51263 → 35.190.46.17:https (GCP)

netstat -v -p tcp | grep 10994
# → Both connections: Send-Q=0, Recv-Q=0
#   (first two columns after tcp4)
```

**Key insight:** ESTABLISHED connections + 0 Send-Q + 0 Recv-Q = connections are alive but **no data is flowing**. A working Claude would have non-zero Recv-Q (receiving API responses) or at least periodic Send-Q bursts. 0/0 means the connections are pure keepalive — no productive work in progress.

#### 4. Session file growth — definitive negative signal

```bash
SIZE1=$(stat -f%z ~/.claude/projects/-Users-fausto/fb9d5594-*.jsonl)
# → 1406420
sleep 30
SIZE2=$(stat -f%z ~/.claude/projects/-Users-fausto/fb9d5594-*.jsonl)
# → 1406420
Delta: 0 bytes
```

Zero bytes growth in 30 seconds with 69% CPU = definitive stuck loop. The file's last modification time was Jul 3 01:01 (36 minutes before the check).

#### 5. Project file check — no source modifications

```bash
# Check if any AgentTalk files changed (CWD was home, but Claude could still work elsewhere)
find ~/Software/AgentTalk -name "*.ts" -mmin -120 -type f 2>/dev/null | head -5
# → (empty)

# Check git log for recent commits
cd ~/Software/AgentTalk && git log --oneline --since="6 hours ago" 2>/dev/null | head -10
# → Only commits from other agents (Codex/docs), none from this PID
```

The Claude session wasn't writing to any project. No recent commits from this PID.

#### 6. Open files — only runtime resources

```bash
lsof -p 10994 | head -20
# → Binary mapping, ICU data, .node temp, /dev/ttys004 I/O, 2 IPv4 sockets
```

No session `.jsonl` files open (no active project), no regular files being written. The only writable FDs are `/dev/ttys004` (the terminal it runs in) — the process is sleeping at the prompt.

### Classification

| Category | Signal | Finding |
|----------|--------|---------|
| PPID | zsh (live) | Not orphaned |
| CPU | **69%** | Well above idle threshold |
| Connections | 2 ESTABLISHED, 0 Send-Q, 0 Recv-Q | **Idle keepalive — no data flowing** |
| Session .jsonl | 0 bytes growth in 30s | **Definitive stuck signal** |
| Project modifications | None | No work output |
| Open files | No session file, only runtime FDs | Sitting at prompt |
| CPU time vs elapsed | 20m / 8.5h (4%) | Low ratio for claimed runtime |

**Verdict: ⚠️ Stuck/heartbeat loop.** The CPU (69%) is real but futile — likely spinning on keepalive API calls, the same pattern documented for agy. The 0 Send-Q/0 Recv-Q on established connections confirms no productive data transfer. Zero session file growth is the definitive negative signal.

### Decision tree — Claude specific

```
Find claude orphan with high CPU
    │
    ├─ Check PPID ancestry
    │   ├─ PPID=1 → true orphan (kill)
    │   └─ PPID=zsh → manual iTerm launch, go to network check
    │
    ├─ Check network connections:
    │   ├─ `lsof -p <PID> | grep ESTABLISHED`
    │   │   ├─ 0 connections → frozen/stuck (codex rule; for Claude also definitive)
    │   │   └─ ≥1 connections → go to Send-Q/Recv-Q check
    │   │
    │   └─ `netstat -v -p tcp | grep <PID>` — check Send-Q and Recv-Q:
    │       ├─ Non-zero Recv-Q → data flowing in = WORKING
    │       └─ 0 Recv-Q AND 0 Send-Q → idle keepalive, go to session file check
    │
    ├─ Check session .jsonl growth over 30-60s:
    │   ├─ Growing → LEGITIMATE WORK
    │   └─ Flat → STUCK LOOP (especially if CPU >10%)
    │
    └─ Check project file modifications + git log:
        ├─ Recent uncommitted changes or commits → WORKING
        └─ No changes → confirmed stuck
```

### Key commands for Claude investigation

```bash
# 1. Network data flow check (Send-Q / Recv-Q columns)
netstat -v -p tcp | grep <PID>
# First two columns after tcp4: Recv-Q Send-Q
# 0 0 = idle keepalive, no activity

# 2. Session file growth (definitive)
SIZE1=$(stat -f%z ~/.claude/projects/*/*.jsonl 2>/dev/null | sort -rn | head -1)
sleep 30
SIZE2=$(stat -f%z ~/.claude/projects/*/*.jsonl 2>/dev/null | sort -rn | head -1)
echo "Delta: $((SIZE2 - SIZE1)) bytes"

# 3. File modification check
find <project_dir> -mmin -60 -type f -not -path '*/.git/*' | head -10

# 4. CPU-to-elapsed ratio
ps -o pid,etime,%cpu,time -p <PID>
# time / etime ≈ 0.04 = 4% utilization over lifespan — low for 69% current CPU
# time / etime ≈ 0.50+ = sustained high utilization over lifespan — more likely legitimate
```

### Comparison with agy stuck loop

| Aspect | agy | Claude |
|--------|-----|--------|
| Log signal | `loadCodeAssist` / `fetchAvailableModels` | No text log available |
| Definitive proof | `HandleUserInput called with text:` in log | Session .jsonl growth over 30s |
| Network signal | Single keepalive connection | Multiple ESTABLISHED with 0 Send-Q/Recv-Q |
| Open file clue | 244 project JSONs (loading context) | Only runtime FDs if stuck |
| Kill safety | Check for streamGenerateContent first | Check .jsonl growth first |

### What was learned (agy — PID 11528)

1. **`HandleUserInput` is the definitive signal for agy** — it directly proves a user sent a task. No other metric overrides it.
2. **Rapid `streamGenerateContent` with unique ResponseIDs ≠ loop** — it's legitimate work. The loop pattern is `loadCodeAssist`/`fetchAvailableModels` without stream calls.
3. **CPU should trend DOWNWARD** for a finishing process. Stable or escalating CPU despite elapsed time = possible loop.
4. **Claude session file growth check** — 15 seconds was enough to confirm idle (0 bytes delta). The 60-second recommendation in the main protocol is the safe default; 15s works when CPU is already <1%.
5. **Codex IDE extension** (`app-server --analytics-default-enabled` under Antigravity Helper) is a repeatable false positive — ignore.

### What was learned (Claude — PID 10994)

1. **Send-Q/Recv-Q from `netstat -v` is a better network idle signal than `lsof` alone** for Claude. `lsof` shows connections as `ESTABLISHED` even when no data is flowing for minutes. `netstat -v` shows the actual pending data queues — a Claude that has 0 Recv-Q (nothing pending from API) and 0 Send-Q (nothing pending to send) for a sustained period is idle or stuck, even with connections marked ESTABLISHED.
2. **Session .jsonl growth is the definitive Claude signal** — same as stated in the main protocol, confirmed here with a 30-second sample (0 bytes delta = definitive stuck).
3. **Project file modifications + git log are useful cross-checks** when .jsonl data is ambiguous (e.g. multiple projects, or CWD matches a project with stale session files).
4. **CPU-to-elapsed ratio** (`time/etime`) is a useful secondary metric: 4% utilization over 8.5h means the 69% CPU spike is very recent or intermittent — not sustained work.


