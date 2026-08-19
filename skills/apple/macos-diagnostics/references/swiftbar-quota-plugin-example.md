# AI CLI Quotas — real-world SwiftBar + API server example (two-endpoint architecture)

## Architecture

```
quota_api.py (launchd service, port 9899)
  │
  ├── background_fetch_loop (daemon thread):
  │     tick 1..N (every ~2 min):
  │       1. Fetch Claude transcript token totals (lightweight, file reads)
  │          → updates /tokens cache
  │       2. Every 5th tick (~10 min):
  │          a. Claude interactive /usage (tmux) → /usage cache
  │          b. Codex interactive /status (tmux) → /usage cache
  │          c. Antigravity interactive /usage (tmux) → /usage cache
  │          d. Compute aggregate max_used_percent across providers
  │
  ├── GET /tokens  → Claude transcript token totals (every ~2 min)
  └── GET /usage   → Usage % for Claude, Codex, Antigravity + aggregate

Display surfaces (read-only, never trigger a fetch):
  ├── SwiftBar plugin (ai_quotas.30m.sh) → curls /usage
  └── quotas.html → fetches both /tokens and /usage every 30s
```

**Key principle**: the background loop writes to cache; endpoints only read from cache. No request ever blocks on a fetch. This keeps SwiftBar instant and avoids focus-stealing.

**Cache cleanup**: `raw_text` fields from tmux-scraped data are stripped at cache time via `_strip_raw()` so payloads stay small.

## Files

- **API server**: `~/Software/scripts-ai/quota_api.py`
- **SwiftBar plugin**: `~/Software/scripts-ai/swiftbar/ai_quotas.30m.sh`
- **Shared lib**: `~/Software/scripts-ai/ai_quota_lib.py`
- **HTML dashboard**: `~/Software/scripts-ai/quotas.html`
- **LaunchAgent**: `~/Library/LaunchAgents/com.fausto.claude-api.plist`

## Endpoint formats

### GET /tokens

```json
{
  "claude": {
    "ok": true,
    "tokens_last_30_days": {
      "files": 120,
      "messages_with_usage": 6754,
      "totals": {
        "input_tokens": 1033677,
        "cache_creation_input_tokens": 31435366,
        "cache_read_input_tokens": 1746479264,
        "output_tokens": 9112432
      }
    }
  },
  "last_update": 1782133270.867
}
```

### GET /usage

```json
{
  "claude": {
    "ok": true,
    "parsed": {
      "current_session": { "used_percent": 82, "resets": "5:10pm (Europe/Rome)" },
      "current_week_all_models": { "used_percent": 78, "resets": "Jun 24 at 9am (Europe/Rome)" }
    }
  },
  "codex": {
    "ok": true,
    "parsed": {
      "five_hour_limit": { "left_percent": 99, "used_percent": 1, "resets": "20:01" },
      "weekly_limit": { "left_percent": 20, "used_percent": 80, "resets": "08:43 on 25 Jun" }
    }
  },
  "antigravity": {
    "ok": true,
    "parsed": {
      "models": [
        { "label": "Gemini Models (Weekly Limit)", "left_percent": 5, "used_percent": 95 },
        { "label": "Gemini Models (Five Hour Limit)", "left_percent": 96, "used_percent": 4 }
      ],
      "highest_used_percent": 95
    }
  },
  "aggregate": {
    "max_used_percent": 95,
    "providers": ["claude", "codex", "antigravity"]
  },
  "last_update": 1782133270.867
}
```

## Plugin output format (menubar header)

```
🟩🟩🟩  🟩🟩🟩 | tooltip='Claude: Session 90% (Week: 88%) | ...'
```

- First 3 squares = session remaining bars (Claude | Codex | Antigravity)
- Second 3 squares = weekly remaining bars
- Color: 🟩 ≥40% remaining, 🟨 20-39%, 🟥 <20%, ⬛ offline

## Fixes applied

### Focus fix
Originally the API server's background loop called `open swiftbar://refreshplugin?name=ai_quotas.2m.sh` after every fetch (forced refresh = focus steal every ~2 min). The plugin also had a `.2m` suffix, so both the timer and the URL scheme raced.

Fix:
1. **Removed the `swiftbar://refreshplugin` call** from the API server background loop
2. **Renamed the plugin** from `.2m` to `.30m` to lower auto-refresh frequency
3. Refactored to **two endpoints** (`/tokens` lightweight, `/usage` heavy) so the SwiftBar plugin reads from cache only — no tmux scraping, no blocking, no focus steal

### CORS fix
The HTML dashboard (`quotas.html`) is opened from `file://`. The browser blocks `fetch()` to `http://127.0.0.1:9899` from a `null` origin unless the server sends:

```python
self.send_header("Access-Control-Allow-Origin", "*")
```

### Antigravity parser fix
The original parser used `([0-9]{1,3})%` which on `5.10%` matched `10` (decimal part) instead of `5`. Fixed to `([0-9]+(?:\.[0-9]+)?)%` with `int(float(match))`. Also added model group tracking so "Weekly Limit" entries are correctly labeled as "Gemini Models (Weekly Limit)" instead of appearing as model names.

### raw_text stripping
Tmux-scraped data carries a `raw_text` field with the full terminal buffer (2-10 KB). This is stripped from the cached data by `_strip_raw()` before storing, keeping response payloads small.

## HTML dashboard layout

The `quotas.html` file shows both endpoints in side-by-side panels with auto-refresh every 30 seconds:

```
┌──────────────────────┬──────────────────────┐
│  GET /tokens         │  GET /usage           │
│  (Claude transcripts)│  (Claude/Codex/Agy %) │
│  refreshes ~2 min    │  refreshes ~10 min    │
│  web refreshes 30s   │  web refreshes 30s    │
└──────────────────────┴──────────────────────┘
```