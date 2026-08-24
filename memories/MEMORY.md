HOT quick-ref: HMP send=curl POST <ip>:18643/hmp/send + poll /hmp/poll/{id}; Charon=peer70=192.168.178.70; this Mac=peer128 on home LAN 192.168.178.112 (WireGuard NOT needed, verified 2026-08-23); Antigravity agy=~/.local/bin/agy.
§
adapter peer136 v0.1.5 6fc19e0f (mesh-consistent: peer70 runtime + peer136 + my g0-bundle). G0 baseline = b9525a0b (peer70 g0-bundle, v0.1.4-g0-g2b-v7); ref hash c164ba7a is STALE (corrected in skill 2026-08-23). Byte-diff b9525a0b→6fc19e0f VERIFIED by me: 3 changes (event-store resolution hardening + 2 version bumps), ZERO G0-core change — G0-1 no-regression now PROVEN by diff.
§
loop-coding-guidelines skill (rinominato da code-dev-reviewer 2026-08-19; PENDING propagate a peer70/141).
§
Anthropic: Fausto vuole usare i modelli Anthropic SOLO via subscription Claude (Pro; flusso `claude setup-token` OAuth / CLAUDE_CODE_OAUTH_TOKEN) — NIENTE API key diretta, NIENTE relay Nous (scelta esplicita 2026-08-20). Claude CLI installato a ~/.local/bin/claude (credenziali non ancora salvate; auth status: logged out). Desiderata non configurato: main=claude-opus-4-8 via subscription, fallback=deepseek-v4-flash.