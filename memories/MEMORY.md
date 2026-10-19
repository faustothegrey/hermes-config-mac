Charon flappa (4-ott): 36 failover / 36 recovery. Sidecar watchdog triggera falsi failover mentre Charon è UP.
§
adapter peer136 v0.1.5 6fc19e0f (mesh-consistent: peer70 runtime + peer136). G0 baseline = b9525a0b (peer70 g0-bundle, v0.1.4-g0-g2b-v7). Byte-diff b9525a0b→6fc19e0f: 3 changes (event-store hardening + 2 version bumps), ZERO G0-core change — no-regression PROVEN by diff.
§
loop-coding-guidelines skill (rinominato da code-dev-reviewer 2026-08-19; PENDING propagate a peer70/141).
§
Claude CLI a ~/.local/bin/claude. Su macOS la CLI legge le credenziali dal Keychain (item 'Claude Code-credentials'), NON da ~/.claude/.credentials.json (formato Linux) -> token valido nel JSON dà comunque loggedIn:false. Fix per servizi headless: setup-token (token lungo sk-ant-oat) iniettato in env. 2026-08-28: token in ~/.zshrc riga 120 + in EnvironmentVariables del plist launchd com.fausto.claude-api (quota-monitoring); reload launchctl da fare a mano (gateway blocca bootstrap). Desiderata non configurato: main=claude-opus-4-8 via subscription, fallback=deepseek-v4-flash.
§
Mesh A2A (2026-09-06): POST /v1/runs (NON /v1/hrpl/chat=completion senza agent loop). Body {input, instructions=identità+ruolo, session_id=thread_id, conversation_history opz}. thread_id=thr-<slug>-<≥12hex>; 1 thread→N run. 202=solo accettato→polling GET /v1/runs/{run_id} a stato terminale + output reale. HMP=fallback offline. Su peer128: /v1/runs su porta 8642 (NON 8765 morto); Bearer API_SERVER_KEY (64char) dal dotenv ~/.hermes, NON la 12char di config.yaml (401). GET /v1/runs=405 (nessuna route di listing). Audit live read-only: gateway_state.json active_agents + state/gateway.heartbeat + processes.json + cron/jobs.json (NON state.db).
§
HMP phantom flap (7-ott, 1300x): solo ack terse. Escalation rifiutata. Verifica solo su 2 FAILOVER consecutivi. Sidecar_state.json su peer58.
§
HMP failover genuino 8-ott + RECOVERY 18-ott: Charon peer70 registry sync fallito (1367x), registry su peer58. RECOVERY OK — Charon rientrato, sidecar rientrato a mirror in entrambe le occasioni.
§
Charon registry sync in flapping: 1852→1885 (+1/episodio), poi counter resettato a 6 (riavvio Charon?)