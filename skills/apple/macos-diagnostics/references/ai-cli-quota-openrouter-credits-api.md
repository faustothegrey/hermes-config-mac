# OpenRouter Credits API

Endpoint: `https://openrouter.ai/api/v1/credits`
Auth: Bearer token from shell env (`zsh -ic 'echo "$OPENROUTER_API_KEY"'`)
Response:
```json
{"data": {"total_credits": 25, "total_usage": 0.0623532}}
```

Remaining = `total_credits - total_usage`

Key is exported in `~/.zshrc`, NOT in `~/.hermes/.env`. The `/auth/key` endpoint returns per-key limits (not account balance) — use `/credits` for account-level data.
