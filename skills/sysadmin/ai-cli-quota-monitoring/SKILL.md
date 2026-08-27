---
name: ai-cli-quota-monitoring
description: "Use when working on AI CLI quota monitoring on port 9899."
version: 1.1.0
author: curator
license: CC-BY-4.0
metadata:
  hermes:
    tags: [quota, tmux, monitoring, claude, codex, antigravity, openrouter, systemd]
---

# AI CLI Quota Monitoring

## When to Use

- Working on the local AI CLI quota service (endpoints /tokens, /usage on 127.0.0.1:9899) — extending it, fixing scrapes, adding providers.
- Debugging tmux-driven capture of interactive CLIs (Claude Code /usage, Codex /status, Antigravity /usage).
- Moving/porting the scripts-ai stack between hosts or pulling it from the NAS.
- Setting up or troubleshooting the quota-api systemd user unit.

Local service tracking AI CLI usage quotas (Claude Code, Codex, Antigravity, OpenRouter) served over HTTP on 127.0.0.1:9899.

## Availability on the mesh (coordinator node)

- **peer70 "Charon" (192.168.178.70) is the coordinator and runs this service** as
  the systemd user unit `quota-api.service`. If you are on another mesh node and
  need quota data, look here first before setting up your own scrape stack.
- The HTTP server binds to **127.0.0.1 only** — it is NOT reachable over the LAN.
  From another peer, query it via SSH to the coordinator:
  ```bash
  ssh fausto@192.168.178.70 'curl -s http://127.0.0.1:9899/usage'   # or /tokens
  ```
- Verify the unit is up without touching it: `ssh fausto@192.168.178.70 "systemctl --user is-active quota-api.service"` → `active`.
- To run the service locally on a peer instead: source lives on the NAS
  (`Software/scripts-ai/...`), copy `quota-monitoring/` + `ai-quota-lib/` to
  `~/scripts-ai/`, fix macOS→Linux paths (see Porting section), create the
  user unit, enable linger. Do NOT enable it on another node without the
  coordinator's OK — one coordinator instance is the mesh default (Fausto policy:
  no unsolicited changes to other nodes).

## Architecture

- quota-monitoring/ — the HTTP service
  - api.py — HTTPServer on 127.0.0.1:9899, two endpoints:
    - GET /tokens — Claude transcript token totals (light refresh, every ~2 min)
    - GET /usage — usage % per provider (heavy, every ~10 min = every 5th 2-min tick)
  - Endpoints read a pre-filled cache (dict + threading.Lock); background_fetch_loop() fills it — no request blocks on a fetch.
  - lib.py is a backward-compat shim: `from ai_quota_lib import *`
  - scripts/{claude,codex,antigravity} — CLI wrappers around ai_quota_lib
  - telemetry.py — reads http://127.0.0.1:9899/usage
- ai-quota-lib/ — shared package (pyproject, name=ai-quota-lib, requires-python>=3.9)
  - ai_quota_lib/__init__.py — all logic in one file (~620 lines)
  - resolve_command() finds CLIs via shutil.which, then ~/.local/bin, ~/bin, nvm dirs
  - Config dirs: ~/.claude (CLAUDE_CONFIG_DIR), ~/.codex (CODEX_HOME), ~/.gemini/antigravity-cli (ANTIGRAVITY_HOME)
- Codex quota sourced ONLY from the live interactive /status screen (tmux scrape); Claude from interactive /usage + local transcripts; Antigravity from interactive /usage (exposes only the 5h model-quota window).

## File locations

- Source of truth: NAS FRITZ!Box 192.168.178.1, share FRITZ.NAS, path Software/scripts-ai/... (SMB via smbclient)
- Local Linux working copy: /home/fausto/scripts-ai/{quota-monitoring,ai-quota-lib} (NAS copy had macOS /Users/fausto/... hardcoded)
- systemd user unit: ~/.config/systemd/user/quota-api.service
- Logs: ~/.hermes/logs/quota-api.log

## Service management

```bash
systemctl --user restart quota-api.service
systemctl --user status quota-api.service
curl -s http://127.0.0.1:9899/usage | python3 -m json.tool
```

Unit is enabled, Restart=always; user linger active so it starts at boot. Note: restarting the unit while the old process still holds the port makes the unit loop with "Address already in use" — kill leftover api.py PIDs first.

## tmux scrape technique (how heavy fetchers work)

Run the CLI in a detached tmux session, send keys, capture-pane text, parse, kill session.

- new-session -d -s <name> -x 140 -y 45 -c <workdir> <cli>
- send-keys to drive the TUI; capture-pane -p -S -N for scrollback
- Always kill-session in a finally block; session name includes pid+time to avoid collisions

## Pitfalls (learned the hard way)

1. FIRST-RUN PROMPTS SWALLOW KEYSTROKES: Claude Code shows a "fullscreen renderer" prompt on first run, then a "trust this folder" dialog. A single Enter hits the renderer prompt, not trust. FIX: capture-pane early (~5s) and grep for "fullscreen renderer"; if present send "2" (Not now), then Enter for trust, then /usage.
1b. CODEX "UPDATE AVAILABLE" PROMPT BREAKS THE SCRAPE (codex ok:false, parsed {}): on a fresh tmux session Codex shows "Update available! X -> Y" with option 1 "Update now" pre-selected; the first Enter (meant for the trust dialog) confirms the update, Codex starts downloading, and the later /status keystrokes land in the shell mid-download → capture shows "Updating Codex CLI..." + a literal "/status". FIX (root cause): add `check_for_update_on_startup = false` to ~/.codex/config.toml at TOP LEVEL (not inside a [projects."..."] table — TOML would scope it to that project). Verify with `codex_interactive_status()` → ok:True. Note: a stray run can half-update the binary (still old version) — harmless, kill the tmux session to abort.
2. ESCAPE KILLS THE APP: sending Escape to dismiss a dialog exits Claude entirely (subsequent capture is empty). Never send bare Escape — use a numbered answer + Enter.
3. First usage cycle is SLOW and sequential: claude + codex + antigravity + openrouter fetches can take ~100s. Don't declare failure until the log shows "Usage fetch done" — watch the log, not just curl.
4. /usage returns ok:False with error:None when the scrape succeeded but the parser found no expected fields (TUI never reached the screen) — debug by capturing raw pane text.
5. Missing provider CLIs return graceful JSON errors ("command not found: X"), NOT crashes — the aggregate just ignores that provider.

## Porting macOS → Linux (this project originated on macOS)

- api.py had hardcoded sys.path.insert("/Users/fausto/Software/scripts-ai/...") → change to /home/fausto/scripts-ai/...
- fetch_openrouter_credits ran `zsh -ic 'echo "$OPENROUTER_API_KEY"'` → zsh absent on this box, use bash -ic
- launchd plist (com.fausto.claude-api.plist) → replicate as systemd user unit with Environment=PATH incl. ~/.local/bin
- ai_quota_lib itself was already portable (Path.home(), resolve_command) — no /Users refs

## NAS access (when the CIFS mount goes stale)

- ~/Software is a CIFS mount of FRITZ.NAS/Software (fstab). It can go stale ("Stale file handle", "Device or resource busy" on unmount). When it does, bypass the mount with smbclient to pull files:
  `smbclient //192.168.178.1/FRITZ.NAS -U 'fausto%ccll4372' -c 'cd Software/scripts-ai/quota-monitoring; recurse ON; prompt OFF; mget *'`
- Clean macOS junk after download: `find . -name '._*' -delete; rm -rf __pycache__` (drop .git too unless history is wanted)
- For quick reads of a busy mount: smbclient `get` the file to /tmp, then read it there.

See references/provider-scrape-quirks.md for the detailed scrape debugging log and exact working key sequences.
