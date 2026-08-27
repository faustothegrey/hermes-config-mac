# Provider scrape quirks (debugging log 2026-08-26/27)

## Claude Code interactive /usage via tmux

Environment: Claude Code v2.1.247 on Debian 13 (trixie) arm64, claude in ~/.local/bin.

First-run sequence observed:
- Start shows a "fullscreen renderer?" prompt (1. Yes / 2. Not now) AND a "trust this folder" dialog.
- Sending a single Enter only confirms the renderer prompt; a subsequent /usage lands on the
  welcome screen, and the parser returns ok:False / current_*:None.
- Sending Escape to dismiss a dialog KILLS the app (subsequent capture-pane is empty).

Working key sequence (patched into claude_interactive_usage):
```
tmux new-session -d -s S -x 140 -y 45 -c /home/fausto <claude>
sleep 5
# early capture to detect the first-run renderer prompt
if "fullscreen renderer" in capture-pane -p -S -40:
    send-keys "2"     # "Not now"
    sleep 1
send-keys Enter        # accept the trust dialog
sleep 2
send-keys /usage Enter
sleep 8..25            # give the /usage screen time to render
capture-pane -p -S -220
kill-session
```

Observed successful parse: current_session 4% (resets ~9:40am Europe/Rome),
current_week_all_models 16% (resets ~Sep 2 9am Europe/Rome).

Note: the renderer prompt appears only on first run (Claude remembers the choice), so the
early-capture guard is cheap and idempotent.

## Codex interactive /status via tmux

- Works out of the box once codex is installed; account Plus status + model line.
- Fields: five_hour_limit (resets e.g. "00:57 on 27 Aug"), weekly_limit (resets e.g. "19:37 on 1 Sep").
- Home dir: ~/.codex (CODEX_HOME).

## Antigravity

- Binary is `agy` — resolve_command("agy"), NOT "antigravity".
- Home dir: ~/.gemini/antigravity-cli (ANTIGRAVITY_HOME).
- parse_antigravity_interactive_usage exposes highest_used_percent; the CLI /usage only
  exposes the 5h model-quota window.
- Returns highest_used_percent: 0 when the account is untouched.

## OpenRouter

- fetch_openrouter_credits reads OPENROUTER_API_KEY from an interactive shell via
  `bash -ic 'echo "$OPENROUTER_API_KEY"'` (was zsh on macOS).
- If unset → ok:False "OPENROUTER_API_KEY not found in shell env". To enable, add the key to
  the quota-api systemd unit Environment= (or export it in the user shell).

## Aggregate

- compute_aggregate() = max used_percent across claude (session + week), codex (5h + week),
  antigravity (highest). providers list = only providers that returned ok + parsed.

## Timing / refresh

- background_fetch_loop: tick every ~120s; /tokens refreshed every tick; /usage on tick 1
  then every 5th tick (~10 min).
- First usage cycle after service start can take ~100s (sequential provider fetches).
- Providers missing their CLI report graceful JSON errors and are excluded from aggregate —
  never a crash.
