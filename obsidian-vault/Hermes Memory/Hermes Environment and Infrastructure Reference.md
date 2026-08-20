# Hermes Environment & Infrastructure Reference

Full details for infra facts kept only as pointers in hot memory. Update here when infra changes.

## Mac config backup
- Repo: `~/Backups/hermes-config/` → `git@github.com:faustothegrey/hermes-config-mac.git`
- Schedule: nightly 00:30 (cron job `b763d78565da`)
- Script: `~/.hermes/scripts/hermes-config-backup-nightly.sh` → `scripts/backup-hermes.sh`
- Backs up: config, skills, cron, profiles, plugins, memories, hooks, Obsidian vault, inventory
- **Secrets are LOCAL-ONLY (fix 2026-08-19):** `secrets/` is `.gitignored` and NOT pushed. The nightly encrypted-bundle step is SKIPPED unless `BACKUP_SECRETS=1`. Why: it re-encrypted `state.db` (~525MB) every night with a fresh random AES key → 162MB byte-different bundle that git couldn't delta → `.git` bloated to **13GB** → `git pack-objects` at 481% CPU for 22 min overheated the Mac (load 23). Fix: `.gitignore secrets/` + fresh git history (13GB→160MB) + force-push + `BACKUP_SECRETS` opt-in switch. Backup now runs in ~15s. To include encrypted secrets off-site again: run with `BACKUP_SECRETS=1` (but expect .git regrowth — better to snapshot secrets separately if ever needed).
- Crypto (when enabled): SSH RSA + OpenSSL AES-256-CBC envelope encryption

## hermes-live-transcript
- Managed by launchd: `com.fausto.hermes-live-transcript` (KeepAlive), port 8800
- UI: http://127.0.0.1:8800 — plist in repo
- Also: agent-telemetry server (PID ~815), port 9900, `GET /agents` endpoint

## HMP (Hermes Message Protocol) network
- Send: `curl POST <peer-ip>:18643/hmp/send`, poll `/hmp/poll/{id}`
- Charon = peer70 = 192.168.178.70
- WireGuard VPN server: peer58 (192.168.178.58), wg0 10.0.0.1/24:51820
- peer128 = 10.0.0.6
- DDNS: settembre2.homepc.it
- Tunnel up: `sudo wg-quick up wg-peer128`
- FritzBox forwards 51820/UDP → peer58

## Daily Exchange (peer digest)
- 03:30 via HMP. Charon (peer70) asks; reply 3–4 sentences: skill modificate, bug fix, pattern, limiti
- Max 2048 char. Chunking: `digest_id` + `chunk`
- Peer84 reachable only 17:00–02:00

## AgentTalk
- Scrum-Master delegate model. Roles: PO (Fausto) / Architect (Claude) / Planner (Codex) / Reviewer (Claude) / Implementer (Gemini)
- Orchestrator API: port 3741 (launchd)
- Agents commit freely (PO-gated merge); SM greenlights
- Session close: agents write lessons + keys
- Operator-seat skill: repo `design/operator-seat/` (symlinked into `~/.hermes/skills`)

## Heartbeat (agent-wait safety net)
- Write a timestamp file when waiting on agents
- Cron `hermes-heartbeat` (1 min) checks stale >5 min → warns conversation + Telegram via `origin,all`
- One notification per stuck period

## Backlog / future ideas
- **Peer messaging over Telegram (later):** stand up a shared Telegram group with the peer bots joined, then address specific peers with `@`-mentions / specialized message syntax (cf. the `yuanbao` group @mention pattern). Would let Fausto + peers share one channel. NOT the mesh control plane (that stays HMP `/hmp/send`+`/hmp/poll`); this would be a broadcast room, not addressed request/response. Not configured yet — idea only.

## Dev-agent launching
- Antigravity CLI: `~/.local/bin/agy` (tmux, interactive). **Ignore** `~/.antigravity/antigravity/bin/agy` (wrong binary).
- When launching dev agents (Claude Code / Codex / Antigravity), autonomously choose the workdir from project context. Full project→dir mapping lives in the `delegation-readiness-checks` skill.
