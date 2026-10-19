# Live runtime / context audit (read-only)

Scenario: a coordinator (Sidecar/peer58 or another peer via A2A) requests a read-only audit of your live Hermes runtime/session state and wants compact JSON back. INSPECTION ONLY — never modify anything, never reveal credentials, tokens, secret-bearing paths, or conversation content.

## Live metric sources (peer-local, on the audited peer)

Reliability order for "is anything active right now":

1. `~/.hermes/gateway_state.json` — gateway supervisor state: `pid`, `gateway_state`, **`active_agents`** (live counter of in-flight agent runs), `platforms.<name>.state` (connected/error). Pair with `~/.hermes/state/gateway.heartbeat` (`pid` + `updated_at`) and `state/gateway.lifecycle.json` to confirm freshness before trusting `active_agents`.
2. `~/.hermes/processes.json` — background agent processes managed by Hermes (`[]` = none).
3. `~/.hermes/cron/jobs.json` — per-job `status`/`state`; look for `running`/`active`/`starting`. `~/.hermes/cron/ticker_heartbeat` + `ticker_last_success` = scheduler liveness (updated each tick).
4. `~/.hermes/sessions/sessions.json` — gateway routing index keyed by `session_key` (`platform:...:chat`). Entries carry `last_prompt_tokens`, `updated_at`, `suspended`, `expiry_finalized`, `active_turn_tokens`. Use it to confirm sessions are IDLE (old `updated_at`), NOT to count live sessions — it only changes on gateway events.
5. `~/.hermes/agent-sessions.json` — live agent-session mirror; can be `{}` (empty) on this setup.
6. `ps aux | grep hermes` — expect only the gateway (`python -m hermes_cli.main gateway`) + stderr_timestamp; anything else = extra agent processes.

Do NOT use state.db token counters for liveness — they are cumulative.

## Read-only endpoint probes

- Gateway api_server (mesh, :8642): `/v1/health` → `{status, platform, version}`. `/v1/runs` is **POST-only** — GET returns `405 Method Not Allowed` (endpoint exists, no listing route). `/v1/models`, `/v1/threads`, `/v1/sessions`, `/openapi.json`, `/docs` → 404.
  - Auth: Bearer **`API_SERVER_KEY`** (64-char) from `~/.hermes/.env`. The 12-char `config.yaml platforms.api_server.extra.key` ("hermes-local") is NOT accepted — auth gate returns `{"error":{"message":"Invalid gateway API key (API_SERVER_KEY)","type":"gateway_auth_error",...}}` or empty body.
- HMP listener (:18643): `/health` → `{status:"ok", service:"hmp-gateway", gateway_adapter:true, node_id, bind}`. No `/status`, `/metrics`, `/openapi`.
- Config facts: `node_id` in `config.yaml`; `model.default` + `model.provider`. Context length: config.yaml has NO `context_length`/`max_tokens` key unless explicitly set → report `null` (provider default applies). `provider_models_cache.json` holds model NAME lists only — no context windows.

## Reply convention (Sidecar A2A audit)

Compact JSON only, Italian, verified data only:
`{peer, configured_default_model, configured_context_length, active_session_count, largest_active_session:{session_id, model_if_known, last_prompt_tokens, context_window_if_known} | null, notes}`

Notes should state: the live source + freshness used (e.g. "active_agents=0, heartbeat 13:51 CEST"), the fact that the audit run itself is a live api_server session not counted by `active_agents`, and any metric not exposed read-only (e.g. per-session prompt tokens).

## Verified trace (peer128, 2026-10-19)

- `hermes status` → model deepseek/deepseek-v4-flash, provider Nous Portal; `config.yaml` has no context_length → null.
- `gateway_state.json` `active_agents: 0`, heartbeat fresh (13:51:36 CEST), `processes.json` `[]`, no cron job running → `active_session_count: 0`, `largest_active_session: null`. The audit conversation itself was the only live run, not tracked by the counter.
- Wrong bearer on :8642 → `Invalid gateway API key (API_SERVER_KEY)`; correct `API_SERVER_KEY` → 405/404 (auth passed).
- `sessions.json` showed 5 HMP DM routes, newest `updated_at` 04:15 same day → all idle, not live.