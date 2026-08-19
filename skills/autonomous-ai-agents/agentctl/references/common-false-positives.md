# Common False-Positive Patterns in agentctl health

## Pattern 1: VS Code / Antigravity IDE `codex app-server`

**Observation:** PID 1162 appears as a codex orphan — basename = `codex`, not in tmux, not registered in agent-sessions.json. Runs since Sunday with 0% CPU.

**Signature:**
```
PID  PPID  COMM
1162  858  /Users/fausto/.antigravity-ide/extensions/openai.chatgpt-26.623.31443-.../codex app-server --analytics-default-enabled
```

**Parent chain:**
```
858   538  Antigravity IDE Helper (Plugin) --type=utility ... (VS Code fork)
  ↓
1162  codex app-server --analytics-default-enabled
```

**Root cause:** The Antigravity IDE (VS Code fork) ChatGPT extension spawns its own `codex` binary (`app-server` mode) that persists for the lifetime of the editor. It is a completely different binary from agentctl's codex (npm-installed). Both share the same process basename `codex`, so `agentctl health` matches it by name and classifies it as orphan (no tmux, no registration).

**How to confirm:**
```bash
# Check parent and arguments
ps -p <PID> -o pid,ppid,args
# 1. Args contain "app-server --analytics-default-enabled" → VS Code extension
# 2. Parent is "Antigravity IDE Helper (Plugin)" → confirmed

# Check it's the Antigravity IDE path, not npm codex
ls -la $(ps -p <PID> -o comm= 2>/dev/null)
# ~/.antigravity-ide/... → VS Code extension
# /usr/local/lib/node_modules/@openai/codex/... → npm package
```

**Severity:** 🟢 Negligible — 0% CPU, < 1% RAM. Will disappear when Antigravity IDE exits. No action needed unless you want a spotless health check (then `kill <PID>`; the extension will restart it when you reopen the IDE).

---

## Pattern 2: Transient orphans from orphaned tmux server

**Observation:** Short-lived agent processes (codex, agy) appear and disappear within 1–3 minutes. Each has PPID pointing to an old tmux server process that is itself orphaned (PPID=1). The health check catches them on one pass but they're gone by the next pass.

**Signature (intermittent, self-resolving):**
```
PID    PPID  STATE
12750 12749  S+     codex              # gone in ~2 min
12749 18800  Ss+    node /usr/local/bin/codex   # gone in ~2 min
12989 18800  Ss+    agy                # gone in ~2 min
```

**Root cause:** An old tmux server started with `agentctl spawn` (e.g. `agent-agy-18797`) but whose session was subsequently destroyed. The tmux server process survives (PPID=1), and any agent spawned through it (e.g. by a prior send/execute still in-flight, or a reconnection attempt) appears briefly as an orphan because the original session registration is gone.

**How to confirm:**
```bash
# 1. Find the orphaned tmux server
ps -p 18800 -o pid,ppid,args
# → PPID=1, args="/usr/local/bin/tmux new-session -d -s agent-agy-XXXXX ..."

# 2. Check that the session it was created for no longer exists
TMUX_TMPDIR=/tmp tmux has-session -t agent-agy-XXXXX
# → "can't find session"

# 3. Check transient children (may already be dead)
ps -o pid,ppid,comm --ppid 18800 2>/dev/null
# → may be empty if they've already died
```

**Severity:** 🟢 Harmless — processes are short-lived, already dead by next health check. The orphaned tmux server itself uses 0% CPU / ~3MB RSS. Can be left alone, or cleaned up with `kill <tmux-server-PID>`.

---

## Pattern 3: codex from `tmux attach -t codex-at` (client process)

**Observation:** A `tmux attach -t codex-at` process lingering in `ps aux` output. Not matched by agentctl health (different basename), but can show up in manual inspection and cause confusion.

```
PID   PPID  STATE  STARTED   COMM
96064 96009  S+    08:39     tmux attach -t codex-at
```

This is just a tmux client (the terminal session attached to the codex pane). Harmless. It's not an agent process.

---

## Pattern 4: Manual agent launch from iTerm / terminal tab (left-open session)

**Observation:** A codex, claude, or agy process appears as orphan in `agentctl health --json` but is sitting idle with low CPU, state `S+`, and a live parent shell (PPID ≠ 1, typically zsh with a tty). The process is running in a user's iTerm tab, not under tmux management.

**Signatures by agent type:**

*codex:*
```
PID   PPID  STATE  %CPU  STARTED           COMM
14364 14363 S+      0.0  Mon Jun 29 15:56  .../codex-darwin-x64/vendor/x86_64-apple-darwin/bin/codex
14363 14034 Ss+     0.0                    node /usr/local/bin/codex
14034 14033 Ss      0.0                    -zsh           ← iTerm tab shell
14033   ...         0.0                    login -fp fausto ttys000
```

*claude:*
```
PID   PPID  STATE  %CPU  STARTED           COMM
10994 45818 S+      1-2%  Thu Jul  2 17:00 claude
45818 45817 S             10:25:44          -zsh (alive, ttys004)
45817 41792 S             login -fp fausto ttys004
```

*agy:* agy runs as the CLI binary directly — no wrapper process. PPID is zsh directly.

**Root cause:** The user opened the agent CLI directly in a terminal tab (iTerm, Terminal.app, etc.) instead of via `agentctl spawn`. Each tool behaves differently at the prompt:
- **codex:** drops to interactive menu (`› Explain this codebase`)
- **claude:** waits at prompt; can stay for hours at 0-2% CPU with no .jsonl growth
- **agy:** exits or goes into heartbeat loop when terminal is not its controlling tty

The health check sees these as orphans because they're not under tmux management. This is **NOT a problem** — no retry loop, no CPU burn, no zombie. It's a deliberate user session left open.

**How to confirm:**
```bash
# 1. Is the parent shell still alive? (PPID ≠ 1 = live shell)
ps -p <PID> -o pid,ppid,args
# zsh parent + tty = live iTerm tab

# 2. What terminal is it on?
ps -p <parent_zsh_PID> -o pid,tty,comm
# e.g. ttys000 → an iTerm tab

# 3. Check tty of the agent process itself
ps -o tty= -p <PID>
# Not '??' = attached to a visible terminal window

# 4. For claude: verify .jsonl is NOT growing (confirms idle, not processing)
SIZE=$(stat -f%z ~/.claude/projects/*/*.jsonl 2>/dev/null | sort -rn | head -1)
sleep 60
SIZE2=$(stat -f%z ~/.claude/projects/*/*.jsonl 2>/dev/null | sort -rn | head -1)
[ "$SIZE" = "$SIZE2" ] && echo "IDLE (no work)" || echo "WORKING"

# 5. For codex: verify state DB is NOT growing and ZERO network connections
lsof -p <codex_PID> 2>/dev/null | grep -c 'ESTABLISHED'
# 0 connections + no state file growth = stuck/frozen, not just idle
```

**Distinction from other patterns:**
| Feature | This pattern (manual launch) | Pattern 2 (transient orphan) | Orphaned iTerm (PPID=1) |
|---------|---------------------------|---------------------------|------------------------|
| PPID | User shell (-zsh, alive) | Orphaned tmux server (PPID=1) | PPID=1 |
| CPU | 0-2% (idle or frozen) | 0% but transient | 30-60% (hung/loop) |
| State | S+ (stable, foreground sleep) | S+ (short-lived) | R+ (active, never idle) |
| TTY | `ttysNNN` (visible terminal) | `??` (orphaned) | `??` (orphaned) |
| Duration | Until user closes tab | 1-3 min | Indefinite |
| .jsonl / state growth | Zero over 60s | N/A (transient) | N/A |
| Network (codex) | Zero connections | 0-1 connections | 0-1 connections |
| Action | None / user choice | None (self-resolves) | `kill -9` |

**Severity:** 🟢 Negligible — 0-2% CPU, no resource consumption, it's a live user session. Leave it alone or the user will close the tab themselves. For claude, note that even 1-3% CPU with zero .jsonl growth over 60s is still idle (could be a timed-out API wait or a prompt sitting at input). If you must clean up for a spotless health check, the user can `exit` or `Ctrl+C` in the terminal tab, or you can `kill -9 <PID>` if the session is truly stale.

---

## Pattern 5: Orphaned Python `server.py` (old agent-bus HTTP server)

**Observation:** A Python process running `server.py 8899` with PPID=1 appears in ps output. Not matched by agentctl health (different basename), but appears as an unexpected orphaned daemon during manual investigation.

**Signature:**
```
PID   PPID  STATE  %CPU  RSS   STARTED           COMMAND
69430    1   SN     0.0   6.5M Thu Jul  2 12:43  /Library/Frameworks/Python.framework/.../Python server.py 8899
```

**Root cause:** The old `agent-bus` HTTP server (predecessor to agentctl) was launched at some point and never killed when the architecture was deprecated. The process survived its parent shell (became PPID=1) and continues running as a background daemon. The skill header explicitly states "server.py è morto" but the process was never actually terminated.

**How to confirm:**
```bash
# 1. Check PPID = 1 (truly orphaned)
ps -p <PID> -o pid,ppid,command

# 2. Check if it's actually listening
lsof -p <PID> 2>/dev/null | grep LISTEN

# 3. Check if it's the old agent-bus server
ls -la $(lsof -p <PID> 2>/dev/null | grep cwd | awk '{print $NF}') 2>/dev/null
```

**Severity:** 🟢 Negligible — 0% CPU, < 7MB RSS. No active clients.

**Action (optional cleanup):**
```bash
kill -TERM <PID>
# No side effects — the old server has no active clients.
```

---

## Quick Reference: Classify a codex orphan on sight

| PID | Args / Flags | Parent | Classification |
|-----|-------------|--------|---------------|
| 1162 | `app-server --analytics-default-enabled` | Antigravity IDE Helper | VS Code extension 🟢 |
| 12750 | `/usr/local/lib/.../@openai/codex/.../codex` (no flags) | `node /usr/local/bin/codex` → tmux server (PPID=1) | Transient orphan 🟢 |
| 14364 | `/usr/local/lib/.../@openai/codex/.../codex` (no flags) | `node` → `-zsh` (live shell) → `login ttys000` | Manual iTerm launch 🟢 |
| 72968 | `/usr/local/lib/.../@openai/codex/.../codex` (no flags) | `node` → quota API (PID 655) or tmux; cwd=`/private/tmp/codex-quota-*` | Quota-monitoring transient — **automatically filtered** by agentctl health since 2026-07-04 🟢 |
| 95181 | `/usr/local/lib/.../@openai/codex/.../codex` (no flags) | `node /usr/local/bin/codex` → `script -q` → tmux `codex-at` | Registered agent 🟢 |

> **See also:** `references/quota-monitoring-transients.md` for details on quota-monitoring codex spawns (Pattern 5).
