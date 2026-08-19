# Health Check False Positives — macOS Detection Quirks

Analysis from 2026-06-29 cron session that uncovered two false-positive sources in `agentctl health --json`.

## Anatomy of a false positive

### Scenario: codex running normally, health says DEAD

```
tmux session: codex-at (alive since 08:35)
  pane PID 95179 → script -q ... codex       [comm=script, filtered]
    child 95180 → node /usr/local/bin/codex    [comm=node, not "codex"]
      child 95181 → /usr/local/.../codex      [comm=FULL_PATH, not "codex"]
```

**Bug A:** `ps axo comm` on macOS returns the full executable path for some binaries, not just the basename. `comm != "codex"` failed for PID 95181 because `comm` was `/usr/local/lib/node_modules/@openai/codex/.../codex`.

Fix: `os.path.basename(comm)` normalization before matching.

### Scenario: agy running, health says orphan

```
tmux session: agy-at (alive since 08:43)
  pane PID 96658 → script -q ... agy         [known_pids add: 96658]
    child 96659 → agy                         [comm=agy, matches!]
```

**Bug B:** `known_pids` contained {96658} (the script wrapper), but `find_processes()` returns 96659 (the agy child). PID 96659 ∉ known_pids → classified as orphan.

Fix: `get_descendants(pane_pid)` walks `ps axo ppid,pid` to add all children recursively.

## Detection tree after fixes

```
known_pids = {96658}                          # pane PID (from tmux)
  + get_descendants(96658) = {96659}          # actual agy process
  → known_pids = {96658, 96659}

find_processes("agy") = [{pid: 96659, ...}]
  → 96659 ∈ known_pids → orphan = false ✓
```

## Real vs. false orphan classification

After the fixes, `orphan=true` actually means the process is running OUTSIDE any registered tmux session, not just that it has a different PID than the state file. This is the correct behavior.

### Codex orphans after fix (real, not false)

```
PID  1162  — Antigravity IDE extension (codex app-server)       → harmless, VS Code
PID  86179 — codex in iTerm2 terminal (no tmux wrapper)         → watch, could orphan on tab close
PID  26377 — codex in ai_cli_quotas tmux (unregistered session) → harmless, quota system
PID  95181 — codex in codex-at tmux (registered session)        → known ✓, the managed one
```

## Commands for manual investigation

```bash
# 1. What does ps axo comm actually show for an agent process?
ps axo pid,comm | grep -E '(agy|codex|claude)'

# 2. Check if a process is inside tmux (walk parent chain)
ps -o pid,ppid,command -p <PID>
# If parent chain includes "tmux" or "script -q", it's tmux-wrapped

# 3. List all tmux sessions and their pane PIDs
TMUX_TMPDIR=/tmp tmux list-sessions
TMUX_TMPDIR=/tmp tmux list-panes -t <session> -F "#{pane_pid} #{pane_start_command}"

# 4. Find all descendants of a tmux pane
pane_pid=$(TMUX_TMPDIR=/tmp tmux list-panes -t <session> -F "#{pane_pid}")
ps axo ppid,pid | awk -v pp=$pane_pid '$1==pp {print $2}'  # direct children

# 5. Check orphan status of a process (is PPID=1?)
ps -o pid,ppid,command -p <PID>
# PPID=1 means orphaned from a closed terminal
```
