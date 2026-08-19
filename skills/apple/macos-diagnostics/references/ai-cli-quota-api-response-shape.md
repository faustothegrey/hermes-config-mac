# /usage API Response Shape

Verified response from `http://127.0.0.1:9899/usage`. Last shape update: 2026-06-25 (post-antigravity-parser-fix).

## Top-level structure

```json
{
  "claude": { "ok": true, "parsed": { ... } },
  "codex": { "ok": true, "parsed": { ... } },
  "antigravity": { "ok": true, "parsed": { ... } },
  "aggregate": { "max_used_percent": 100, "providers": ["claude", "codex", "antigravity"] },
  "last_update": "2026-06-25 19:54:27"
}
```

## Claude section

```json
{
  "ok": true,
  "parsed": {
    "session_total_cost_usd": 0.0,
    "session_tokens": { "input": 0, "output": 0, "cache_read": 0, "cache_write": 0 },
    "current_session": {
      "used_percent": 43,
      "resets": "9pm (Europe/Rome)"
    },
    "current_week_all_models": {
      "used_percent": 48,
      "resets": "Jul 1 at 9am (Europe/Rome)"
    },
    "usage_credits": "Usage credits are off · /usage-credits to turn them on"
  }
}
```

Note: `usage_credits` is a string, not a nested object.

## Codex section

```json
{
  "ok": true,
  "parsed": {
    "account": "fausto.lelli@gmail.com (Plus)",
    "model": "gpt-5.5 (reasoning high, summaries auto)",
    "five_hour_limit": {
      "left_percent": 0,
      "used_percent": 100,
      "resets": "22:31"
    },
    "weekly_limit": {
      "left_percent": 70,
      "used_percent": 30,
      "resets": "11:33 on 2 Jul"
    }
  }
}
```

Model name shown as `gpt-5.5` with parens containing config notes.

## Antigravity section (post-fix — all 4 entries, correct window values)

```json
{
  "ok": true,
  "parsed": {
    "window": "5h",
    "current_model": "fausto.lelli@gmail.com (Google AI Pro)",
    "models": [
      {
        "label": "Gemini Models (Weekly Limit)",
        "left_percent": 5,
        "used_percent": 95,
        "window": "weekly"
      },
      {
        "label": "Gemini Models (Five Hour Limit)",
        "left_percent": 100,
        "used_percent": 0,
        "window": "5h",
        "status": "Quota available"
      },
      {
        "label": "Claude And Gpt Models (Weekly Limit)",
        "left_percent": 100,
        "used_percent": 0,
        "window": "weekly",
        "status": "Quota available"
      },
      {
        "label": "Claude And Gpt Models (Five Hour Limit)",
        "left_percent": 100,
        "used_percent": 0,
        "window": "5h",
        "status": "Quota available"
      }
    ],
    "lowest_left_percent": 5,
    "highest_used_percent": 95
  }
}
```

Key changes from the old shape:
- All 4 model entries are now returned (old parser filtered out entries with `left >= 100`)
- `window` is now correct: `"weekly"` for Weekly Limit entries, `"5h"` for Five Hour Limit entries
- Unparsable entries would show `"-"` as string values for `left_percent`/`used_percent`
- `aggregate` skips numeric computation on `"-"` values

## Aggregate

```json
{
  "max_used_percent": 95,
  "providers": ["claude", "codex", "antigravity"]
}
```

`max_used_percent` is the worst across all provider limit sections — used for SwiftBar header bar color thresholding.
