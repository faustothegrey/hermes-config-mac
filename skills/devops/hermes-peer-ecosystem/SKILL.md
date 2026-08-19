---
name: hermes-peer-ecosystem
description: "Inspect, understand, and coordinate with Hermes Agent peers through SSH, MCP peer servers, peer-mesh config, beacon protocol, peer-exchange rounds, and HMP peer messaging. Also covers multi-voice audio talk show production via HMP (edge-tts TTS, live peer turns) and Hermes config backup/disaster recovery (nightly encrypted git backup)."
version: 2.0.0
author: Hermes Agent
license: MIT
platforms: [macos, linux]
---

# Hermes Peer Ecosystem

Use this skill when you need to inspect a remote Hermes peer's running infrastructure, understand the peer mesh topology, read peer-exchange transcripts, or coordinate work across multiple Hermes instances.

## Architecture overview

A Hermes peer ecosystem typically consists of:

| Component | Purpose | Port / Transport |
|-----------|---------|-----------------|
| **Hermes Gateway** | Main agent process, serves API server | 8642 (HTTP) |
| **Beacon Listener** (`beacon-listener.py`) | Registers beacon pings from peers on the LAN | 9191 (HTTP) |
| **MCP Peer Server** (`hermes-peers`) | MCP tools for calling peer API servers | stdio (MCP) |
| **Peer Mesh Config** (`peer-mesh.yaml`) | Peer definitions, URLs, API keys, roles | Config file |
| **Peer Exchange** (`peer-exchange/`) | Structured self-report markdown rounds | Filesystem |
| **Google Workspace / other credentials** | Per-instance OAuth tokens, scoped to each machine | Filesystem |
| **HMP Plugin** (gateway platform adapter) | Hermes Mesh Protocol — direct HTTP messaging between peers via per-peer HMP gateway adapter | 18643 (staging) |

## Key peers in the network

The known peers (from peer84's mesh):

| Peer | IP | Gateway Port | Role | Capabilities |
|------|----|-------------|------|-------------|
| **peer84** (N56VV) | 192.168.178.84 | 8642 | Orchestrator | hermes, lan |
| **peer105** | 192.168.178.105 | 8642 | Worker | hermes, lan |
| **peer128** | 192.168.178.128 | 8642 | Worker | hermes, lan |
| **peer106** | 192.168.178.106 | 8642 | Worker | hermes, lan |

## HMP (Hermes Mesh Protocol) — peer-direct HTTP messaging via gateway plugin

HMP is a lightweight HTTP-based messaging protocol for direct peer-to-peer task dispatch, coordination, and result collection. Each peer runs an HMP **gateway platform adapter** (plugin) that listens for inbound messages and dispatches them through the normal Hermes gateway session machinery. There is no central coordinator bus — POST directly to the target peer's HMP listener.

The plugin is configured via `config.yaml` under `platforms.hmp` (or `hmp` top-level key). It is enabled per-peer and requires the Hermes gateway to be running.

### Architecture

| Component | Detail |
|-----------|--------|
| Listener bind | `platforms.hmp.extra.host` + `port` (staging default: `0.0.0.0:18643`; production target: `8643`) |
| Node identity | `platforms.hmp.extra.node_id` — each peer's name |
| Auth | Shared secret via `shared_secret` / `HMP_SHARED_SECRET`, or `allow_all_peers: true` for open mesh |
| DB | SQLite at `database_path` — stores message status, idempotency keys, and response text |
| macOS firewall | Python sockets blocked on port 8643 — use **curl** from terminal (18643 staging port usually passes) |

### Key endpoints (per-peer, on the HMP listener port)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check — returns status, node_id, bind |
| `/hmp/health` | GET | Same as /health (alias) |
| `/hmp/agent-card` | GET | List available endpoints |
| `/hmp/send` | POST | Send a message — returns `{accepted, message_id, status}` (202: working, 400/403/500: error) |
| `/hmp/send_and_wait` | POST | Send a message and block (up to `request_timeout_seconds`, default 900s) until completed or failed |
| `/hmp/poll/{message_id}` | GET | Poll a message's status — returns full record with `response_text` when completed |

### Sending a message (curl — preferred on macOS)

Since macOS firewall blocks Python outbound on port 8643, use curl via terminal. POST directly to the **target peer**'s HMP listener port:

```bash
curl -s -X POST http://<peer-ip>:18643/hmp/send \
  -H 'Content-Type: application/json' \
  -d '{
    "hmp_version": "1.0",
    "message_id": "req_<from>_<unix_timestamp>",
    "idempotency_key": "req_<from>_<unix_timestamp>",
    "from": "<your_peer_id>",
    "to": "<target_peer_id>",
    "type": "request",
    "status": "pending",
    "timestamp": "'$(date -u +\"%Y-%m-%dT%H:%M:%SZ\")'",
    "payload": {
        "task_type": "chat",
        "message": "Hello!"
    }
  }'
```

On success you get back `{"accepted": true, "message_id": "...", "status": "working"}`.

### Polling for the response

```bash
curl -s http://<peer-ip>:18643/hmp/poll/<message_id>
```

When `status` is `"completed"`, the `response_text` field contains the peer's reply and `sent_to_chat_id` shows where it was routed.

### Message structure

```json
{
  "hmp_version": "1.0",
  "message_id": "msg_abc123",
  "idempotency_key": "unique_key",
  "in_reply_to": "optional_original_msg_id",
  "from": "peer128",
  "to": "peer70",
  "type": "request",
  "status": "pending",
  "timestamp": "2026-07-14T22:00:00Z",
  "payload": { "task_type": "...", "message": "..." }
}
```

Message types: `request`, `response`, `heartbeat`, `ack`, `cancel`.
Task lifecycle states: `pending` → `gateway_accepted` → `working` → `completed|failed|timed_out`.

### Quick health check

```bash
curl -s http://<peer-ip>:18643/hmp/health
# Returns: {"status":"ok","service":"hmp-gateway","gateway_adapter":true,"node_id":"peer105","bind":"0.0.0.0:18643"}
```

### Creative applications — multi-voice audio talk show production

HMP peer messaging can feed into multi-voice audio production. See `references/talk-show-workflow.md` for the complete workflow. Helper scripts under `scripts/` (`sayit.sh`, `send_to_peer.sh`, `wait_for_peer.sh`, `record_peer.sh`) accelerate the live-turn flow.

#### Architecture

```
HERMES_TALKSHOW_DIR=~/voice-memos/hermes-talkshow-live/

[Moderator scripts]  →  sayit.sh        [voice + text → audio + play]
                         record_peer.sh  [voice + text → audio + play]

[HMP integration]    →  send_to_peer.sh  [peer + message → msg_id]
                         wait_for_peer.sh [peer + msg_id → response text]

[Post-production]    →  sox *.mp3 final.mp3
```

#### Voice assignment (Italian)

Use edge-tts Microsoft Neural voices for natural Italian — macOS `say` Italian voices (Eddy, Flo) have English accents and must be rejected for Italian content:

| Role | Voice | Gender | Use case |
|------|-------|--------|----------|
| Moderator/Host | `it-IT-DiegoNeural` | Male | Questions, transitions, closing |
| Guest 1 | `it-IT-ElsaNeural` | Female | First opinionist |
| Guest 2 | `it-IT-IsabellaNeural` | Female | Second opinionist |
| Alt Guest | `it-IT-GiuseppeMultilingualNeural` | Male | Alternative male guest |

For English content, macOS `say` or OpenAI TTS may be sufficient.

#### Show flow (interactive / live)

**Phase 0 — Pre-announce topic (silent HMP):** Send the topic to all guests via HMP *before* the live show starts. This reduces response latency from 10-20s to 3-6s. Wait for "tema ricevuto" confirmation from each guest.

**Phase 1 — Live turns:** For each round: (1) Record + play the moderator's question using sayit.sh (Diego voice), (2) Send the actual question via HMP using send_to_peer.sh, (3) Wait for response using wait_for_peer.sh, (4) Record + play the guest's answer using record_peer.sh (guest voice).

**Phase 2 — Concatenate:** `sox 001_file.mp3 002_file.mp3 ... final.mp3`

#### Segment guidelines

- Keep each segment 30s–2min of speech (~75–500 chars Italian text)
- Number files sequentially (001_, 002_, etc.) for easy sox ordering
- Pre-announce topic reduces wait time without spoiling the specific question

#### Pitfalls

1. **edge-tts pip install** — may need `--break-system-packages` on macOS.
2. **sox concatenation** — files must be listed in order; missing files cause silent truncation.
3. **HMP port** — HMP plugin runs on port 18643 (staging), not 8643.
4. **macOS firewall** blocks Python TCP to port 8643; use curl via terminal for HMP.
5. **Long peer responses** — the `wait_for_peer.sh` polls every 4s; set longer sleep for complex questions.

### HMP Healthcheck (watchdog) — automated peer monitoring

Set up a healthcheck that runs **from a 24/7 peer** (typically peer70, a Raspberry Pi) and monitors all reachable peers' network + HMP availability. The watchdog pattern: silent when healthy, alert only on failure.

#### Architecture

| Layer | Check | Tool |
|-------|-------|------|
| Network | ICMP ping | `ping -c1 -W2` |
| Application | POST to `/hmp/send` | `curl` |

Each peer is checked at both layers so you can distinguish "host unreachable" from "host alive but HMP listener down".

#### Setup on the monitoring peer (native crontab)

Use this when the monitoring peer has no Hermes CLI — set up a native Linux crontab directly:

```bash
# 1. Create the healthcheck script on the monitoring peer
ssh fausto@192.168.178.70 "cat > ~/.hermes/scripts/hmp-healthcheck.sh << 'SCRIPT'
#!/bin/bash
# HMP Healthcheck — runs ON <monitoring-peer>, pings all network peers
# Silent when all healthy. Sends HMP alert to primary peer on failure.

PEER128_HOST=\"192.168.178.112\"
PEER128_PORT=\"18643\"
FAILED=0
ALERTS=\"\"

check_peer() {
  local NAME=\$1 HOST=\$2 PORT=\$3
  local PING_OK=1 HMP_OK=1
  ping -c1 -W2 \$HOST >/dev/null 2>&1 && PING_OK=0
  local HMP=\$(curl -s --max-time 5 http://\$HOST:\$PORT/hmp/send \
    -d '{\"type\":\"ping\",\"from\":\"<monitoring_peer>\",\"timestamp\":\"'\$(date -u +%Y-%m-%dT%H:%M:%SZ)'\"}' \
    -H 'Content-Type: application/json' 2>&1)
  [ \$? -eq 0 ] && HMP_OK=0
  if [ \$PING_OK -ne 0 ] && [ \$HMP_OK -ne 0 ]; then ALERTS=\"\$ALERTS \$NAME:unreachable\"; FAILED=1
  elif [ \$PING_OK -eq 0 ] && [ \$HMP_OK -ne 0 ]; then ALERTS=\"\$ALERTS \$NAME:HMP_down\"; FAILED=1
  fi
}

check_peer \"peer128\" \"\$PEER128_HOST\" \"\$PEER128_PORT\"
# Add other HMP peers:
check_peer \"peer105\" \"192.168.178.105\" \"18643\"
check_peer \"peer106\" \"192.168.178.106\" \"18643\"

TS=\$(date '+%H:%M')
if [ \$FAILED -eq 0 ]; then
  echo \"OK\$TS\" >> ~/.hermes/logs/hmp-healthcheck.log
  exit 0
else
  echo \"[\$TS] FAIL:\$ALERTS\" >> ~/.hermes/logs/hmp-healthcheck.log
  curl -s --max-time 5 http://\$PEER128_HOST:\$PEER128_PORT/hmp/send \
    -d '{\"type\":\"message\",\"from\":\"<monitoring_peer>\",\"to\":\"peer128\",\"text\":\"⚠️  HMP healthcheck: FAIL\$ALERTS\"}' \
    -H 'Content-Type: application/json' >/dev/null 2>&1
  exit 1
fi
SCRIPT
chmod +x ~/.hermes/scripts/hmp-healthcheck.sh"

# 2. Install in crontab
ssh fausto@192.168.178.70 "(crontab -l 2>/dev/null | grep -v hmp-healthcheck; echo '0 * * * * /home/fausto/.hermes/scripts/hmp-healthcheck.sh >> /home/fausto/.hermes/logs/hmp-healthcheck.log 2>&1') | crontab -"
```

#### Setup on the control peer (Hermes cron)

Create a Hermes cron job that SSHes into the monitoring peer and runs the healthcheck, delivering results to your chat:

```bash
# 1. Create a thin wrapper script locally (SSH into monitoring peer)
cat > ~/.hermes/scripts/hmp-peer70-healthcheck.sh << 'SCRIPT'
#!/bin/bash
ssh fausto@192.168.178.70 "cd ~/.hermes/scripts && bash hmp-healthcheck.sh" 2>/dev/null || echo "⚠️  monitoring peer unreachable"
SCRIPT

# 2. Create Hermes cron (no_agent=true, silent when healthy)
# Use cronjob(action='create', name='...', schedule='0 * * * *', script='hmp-peer70-healthcheck.sh', no_agent=true)
```

The Hermes cron variant gives you job visibility (pause/resume/list) and delivers alerts to your conversation. The native crontab is a fallback that keeps monitoring even if Hermes is down.

#### Key design decisions

1. **monitoring peer = peer70** (Raspberry Pi, always on, low power). Do not use a laptop that suspends.
2. **Two layers per peer** — ping (network reachable) + HMP POST (service alive). A peer can be pingable but have its HMP listener down.
3. **Silent when healthy** — the watchdog pattern saves tokens and avoids noise. Only alert on failure.
4. **Dual scheduling** — native crontab on the monitoring peer (resilient) + Hermes cron on the control peer (visible, deliverable).
5. **Log locally** — `~/.hermes/logs/hmp-healthcheck.log` on the monitoring peer for post-mortem.
6. **Ping from peer70 means the healthcheck runs ON peer70** — not "ping peer70 from somewhere else." The phrase "da <peer>" in Italian specifies the source, not the target.

#### Pitfalls

1. **Non-HMP peers produce false alarms.** Only monitor peers known to have the HMP plugin. Skip peers without port 18643 open.
2. **MAC addresses change.** If a peer's IP changes (DHCP), the healthcheck silently misses it. Use hostnames or DHCP reservations.
3. **peer70 may not have Hermes CLI installed.** Use native crontab, not `hermes cron`.
4. **SSH key expires.** The healthcheck via Hermes cron (SSH variant) fails if the SSH key changes. The native crontab is immune.
5. **Watchdog cooldown.** Multiple peers failing at once floods the chat. The script reports all failures in one message.

### Peer-direct curl commands (detailed)

See `references/hmp-curl-commands.md` for exact command examples targeting individual peers.

## Sidecar dual-plane failover (peer58 ↔ Charon peer70)

The HMP fleet uses a **dual-plane** setup: Charon (peer70, 192.168.178.70) is the registry/aggregator **primary**; the Sidecar (peer58, 192.168.178.58) runs a watchdog that mirrors the registry and **promotes itself** when Charon is down, then **demotes back to mirror/fallback** automatically when Charon recovers.

### Architecture

```
peer58 (~/.hermes/scripts/hmp_sidecar.py)
  ├── heartbeat      (every ~3 min via cron no_agent) → checks Charon /hmp/health
  │     ├── 3 consecutive failures → promote()  → broadcast "FAILOVER HMP: ..."
  │     └── Charon ok               → demote_if_charon_back() → broadcast "RECOVERY HMP: ..."
  └── registry_sync  (every ~30 min via cron no_agent) → ingests Charon's registry JSON
```

State lives on peer58 at `~/.hermes/registry/`:
- `sidecar_state.json` — `failover_active`, `promoted_at`, `promotion_reason`, `heartbeat_failures`, `registry_sync_failures`, `last_heartbeat_ok`, `last_registry_sync_ok`, `last_error`
- `mirror.json` — wrapped registry mirror (`mirrored_by`, `mirrored_at`, `registry`)
- `ingested_messages.json` — dedupe list of ingested registry message ids

### Reading the broadcasts (exact texts)

- **FAILOVER**: `FAILOVER HMP: Charon 192.168.178.70 non risponde (<reason>). Registry temporaneo ora su Sidecar 192.168.178.58:18643.` → sidecar promoted itself (`failover_active: true`).
- **RECOVERY**: `RECOVERY HMP: Charon 192.168.178.70 è tornato raggiungibile. Sidecar 192.168.178.58 rientra a mirror/fallback.` → sidecar demoted (`failover_active: false`). **This text is the literal output of `demote_if_charon_back()`** — receiving it means the transition already ran automatically; there is NO manual demote command.

### Verifying a RECOVERY (verify the SIDECAR, not just ping Charon)

A RECOVERY HMP message is an action directive to confirm the sidecar's state transition, not a status notification. Check the sidecar's state file first:

```bash
ssh fausto@192.168.178.58 "cat ~/.hermes/registry/sidecar_state.json"
# expect: failover_active: false, recent last_heartbeat_ok, registry_sync_failures: 0
# promoted_at stays set after demote — historical trace, NOT a failure flag
```

Then confirm Charon is genuinely healthy (two layers): `ping -c 3 -W 2 192.168.178.70` (network) + `curl -s -m 5 http://192.168.178.70:18643/hmp/health` (HMP listener → `{"status":"ok","node_id":"peer70"}`), optionally a round-trip POST to `/hmp/send` polled to `completed`.

### Notes / quirks

- `promoted_at` is NOT cleared by demotion — keep it as evidence of the last failover.
- Peer-id ≠ IP: `peer128` = 192.168.178.112, `trixie`/`peer136` = 192.168.178.136 (mapping in `hmp_sidecar.py` PEERS dict).
- Broadcast skips peer84 during its cooling window (11–17, 2–3).
- Sidecar scripts are cron no_agent jobs: stdout intentionally quiet unless state changes.
- Detailed verification transcript and state examples: `references/sidecar-dual-plane-failover.md`.

## SSH-based peer inspection

When you need to understand a peer's setup, SSH in and probe systematically:

### 1. Check running services

```bash
ssh root@<peer-ip> "ss -tlnp | grep -E '8642|9191|9899'"
```

Look for:
- Port 8642 — Hermes API server (gateway)
- Port 9191 — Beacon listener
- Other service ports

### 2. Check running agent processes

```bash
ssh root@<peer-ip> "ps aux | grep -i 'hermes\|agent\|claude\|codex\|agy' | grep -v grep"
```

Look for:
- `python -m hermes_cli.main gateway run` — main gateway daemon
- `beacon-listener.py` — beacon listener
- `hermes-peers/server.py` — MCP peer server
- Interactive `hermes` sessions

### 3. Check peer mesh topology

```bash
ssh root@<peer-ip> "cat /home/fausto/.hermes/peer-mesh.yaml"
```

### 4. Check peer-exchange directory

```bash
ssh root@<peer-ip> "ls /home/fausto/.hermes/peer-exchange/"
```

The peer-exchange protocol uses structured markdown files:
- `protocol.md` — the exchange protocol specification
- `round-NNN-local.md` — the local instance's self-report
- `round-NNN-peerXXX.md` — other peers' reports
- `round-NNN-synthesis.md` — cross-instance synthesis
- `round-NNN-final-synthesis.md` — finalized synthesis

### 5. Check Google Workspace / credential state

```bash
ssh root@<peer-ip> "ls /home/fausto/.hermes/google_token.json 2>/dev/null && echo 'has google token'"
ssh root@<peer-ip> "ls /home/fausto/.hermes/google_client_secret.json 2>/dev/null && echo 'has google client secret'"
ssh root@<peer-ip> "grep -i 'email\|mail\|smtp\|imap' /home/fausto/.hermes/.env | head -10"
```

### 6. Check skills and config

```bash
ssh root@<peer-ip> "timeout 10 hermes skills list | grep -i <keyword>"
```

### 7. Check gateway capabilities

```bash
# Authenticated via API key:
curl -s -H "Authorization: Bearer <key>" http://<peer-ip>:8642/v1/capabilities
# Gateway allow-all mode:
curl -s http://<peer-ip>:8642/v1/capabilities
```

## MCP Peer Server

The MCP peer server (`hermes-peers`) on each instance provides tools:

| Tool | Purpose |
|------|---------|
| `list_peers(include_health)` | List configured peers, optionally probe health |
| `peer_health(peer, detailed)` | Check a peer's health endpoint |
| `peer_capabilities(peer)` | Get a peer's /v1/capabilities |
| `call_peer(peer, input, ...)` | Send a short synchronous prompt to a peer |
| `start_peer_run(peer, ...)` | Start a long-running task on a peer |
| `get_peer_run(peer, run_id)` | Poll a running task on a peer |
| `get_peer_events(peer, run_id, ...)` | Read SSE events from a peer run |
| `stop_peer_run(peer, run_id)` | Stop a peer run |

Configuration lives in `peer-mesh.yaml`:

```yaml
mcp_servers:
  hermes_peers:
    command: /path/to/python
    args:
    - /path/to/hermes-peers/server.py
    env:
      HERMES_PEER_MESH_CONFIG: /home/fausto/.hermes/peer-mesh.yaml
    timeout: 300
    connect_timeout: 30
```

### API key handling

Peer API keys are stored in `~/.hermes/.env` and resolved by `peer_config.py`:
- Via `HERMES_PEER_<NAME>_KEY` env variable
- Or by reading the `.env` file directly as fallback (MCP subprocesses have filtered environments)

### Peer API Key format

```
HERMES_PEER_105_KEY=hsk-...          # Hyperbolic key (provider API key)
HERMES_PEER_128_KEY=hexstring...     # Hermes API server key
```

**Important:** `hsk-` prefixed keys are **Hyperbolic API keys** (provider keys for LLM routing), not Hermes API server keys. The Hermes API server key is stored in `API_SERVER_KEY` in the peer's `.env`. Do not use a Hyperbolic key as the peer's Hermes API key — the peer API server at `:8642` authenticates with `API_SERVER_KEY`, not with provider keys.

## Beacon Protocol

The beacon listener (`beacon-listener.py`) is a minimal HTTP server on port 9191:

| Endpoint | Purpose |
|----------|---------|
| `GET /beacon/<peer_name>` | Register a beacon ping from a peer |
| `GET /health` | Health check for the listener itself |

Beacons are logged to `~/.hermes/peer-status/beacon.log` with auto-rotation at 2000 lines.

## Peer Exchange Protocol

Peer exchange rounds use a structured self-report format shared via markdown files in `peer-exchange/`. Each round consists of:

1. Each peer writes its own `round-NNN-peerX.md`
2. A synthesis is built from all reports
3. A final synthesis is published

Report structure (from `protocol.md`):
1. System constraints / environment
2. Recurring challenges
3. Goals achieved or useful workflows
4. Failures or pain points
5. Lessons learned / recommendations for other instances
6. What information you would like to receive from peers

**Safety rule**: Do not share API keys, tokens, credentials, raw env dumps, private user content, or sensitive personal data.

## Security & privacy

- **Do not read peer credentials** unless the user explicitly authorizes it — the peer-exchange protocol explicitly forbids sharing secrets
- `.env` files contain API keys — read selectively; only check for specific env var names
- `google_token.json` is an OAuth token — do not read its contents unless debugging auth issues
- **Prefer checking file existence** over reading file contents for credentials

## SSH connection management (sshtmux)

Peer SSH connections are managed via **sshtmux** (`sshm` CLI) — a Python SSH terminal manager that integrates with tmux. It is installed via pip and lives at `/Library/Frameworks/Python.framework/Versions/3.10/bin/sshm`.

### Setup

```bash
pip install sshtmux
ln -sf /Library/Frameworks/Python.framework/Versions/3.10/bin/sshm ~/.local/bin/sshm
```

The SSH config at `~/.ssh/config` is managed by sshtmux with group/comment metadata tags. List hosts with `sshm hosts`, launch the TUI with `sshm tui`.

### Managing hosts

```bash
sshm host create <name> -p Hostname <ip> -p User <user> -p IdentityFile /Users/fausto/.ssh/id_rsa -g <group> -f
```

**Caveats:**
- Param names are PascalCase SSH keywords (`Hostname`, `User`, `IdentityFile`)
- `IdentityFile` must be an expanded absolute path — pydantic's `os.path.exists` doesn't expand `~`
- When a group is specified and the group doesn't exist yet, `-f` (force) auto-creates it
- Hostnames may be prefixed like `lan-peers-peerXX`; rename with `sshm host rename`
- **`sshm host rename strips all parameters`** — the renamed host will have empty Hostname, User, etc. Always follow immediately with `sshm host set` to restore them
- **Empty columns in `sshm hosts`** — after `sshm host set`, the `param:hostname` column may still appear blank even though the SSH config file is correct. This is a display artifact of the table formatter. Verify with `sshm host show <name>` or `cat ~/.ssh/config`

See `references/peer-onboarding.md` for the full key-installation and onboarding workflow.

## Onboarding a new peer (adding to the fleet)

Use this when the user tells you about a new peer on the LAN that needs SSH access set up. See `references/peer-onboarding.md` for the detailed workflow.

### Quick sequence

1. **Test connectivity** — `ssh -o ConnectTimeout=5 fausto@<IP> hostname`
2. **If permission denied** → generate key on Mac (`ssh-keygen -t ed25519 -a 100`), then install via `ssh-copy-id` in **background pty** mode
3. **Interactive password** — use `process(submit)` to feed the password, then `process(wait)` for completion
4. **Add to sshtmux** — `sshm host create peerXX -p Hostname <IP> -p User fausto -p IdentityFile /Users/fausto/.ssh/id_rsa -g lan-peers -f`
5. **Verify** — collect hostname, OS, arch, uptime, memory, disk via SSH
6. **Save** — compact entry in memory (merge with existing peer info to stay under 2,200 chars), full entry in fact_store

### Onboarding is separate from inspection

Inspection assumes the peer is already configured and reachable. Onboarding handles the **first-contact** case where no key is authorized yet. Don't skip step 2 (ssh-copy-id via background pty) — a foreground terminal cannot answer interactive password prompts.

## Hermes Config Backup

Use this section when setting up or troubleshooting the Hermes config backup pipeline — machine disaster recovery for Hermes configuration, skills, cron, profiles, memories, secrets, and the Obsidian vault, stored in an encrypted GitHub repository.

### Architecture

```
Machine (nightly at 00:30, no_agent cron)
  └── hermes-config-backup-nightly.sh
        └── backup-hermes.sh
              ├── generate-backup.py    (sanitized snapshot of config, skills, cron, profiles, etc.)
              ├── encrypt secrets       (SSH RSA + OpenSSL AES-256-CBC)
              └── git commit + push     → GitHub repo
```

### What gets backed up

**Plaintext (redacted):** `config.yaml`, `SOUL.md`, `skills/`, `cron/`, `profiles/`, `plugins/`, `memories/`, `hooks/`, Obsidian vault copy, inventory snapshots.

**Encrypted (never in plaintext):** `.env` (API keys), `auth.json` (OAuth tokens), `gateway_state.json`, `state.db`, Google OAuth files.

Encryption uses OpenSSL AES-256-CBC envelope: random AES key → encrypt tar.gz → SSH RSA public key encrypts the AES key. Both artifacts committed as `secrets/*.enc`.

### Setup procedure

1. Create a private GitHub repo (e.g., `hermes-config-mac`)
2. Clone it to `~/Backups/hermes-config/`
3. Create `scripts/generate-backup.py`, `scripts/backup-hermes.sh`, `scripts/restore-hermes.sh` in the repo
4. Create cron entry-point at `~/.hermes/scripts/hermes-config-backup-nightly.sh`
5. Set up cron job: `cronjob(action='create', schedule='30 0 * * *', no_agent=True, script='hermes-config-backup-nightly.sh')`
6. Run first backup: `cd ~/Backups/hermes-config && bash scripts/backup-hermes.sh`

### Restore procedure

```bash
mkdir -p ~/Backups
git clone git@github.com:username/hermes-config-mac.git ~/Backups/hermes-config
cd ~/Backups/hermes-config && bash scripts/restore-hermes.sh

# With secrets (matching SSH private key needed):
SSH_PRIVATE_KEY=~/.ssh/id_rsa bash scripts/restore-hermes.sh
```

### Verifying backup health

```bash
# Cron job status
hermes cron list | grep -A 10 <job_id>

# Successful commits
cd ~/Backups/hermes-config && git rev-list --count HEAD

# Last commit timestamp
cd ~/Backups/hermes-config && git log -1 --format="%ai %s"

# Uncommitted leftovers (after partial failure)
cd ~/Backups/hermes-config && git status --short
```

Cross-reference: `last_run_at` matching a git commit → success. Git commit count < output directory count → partial failures. `last_status="error"` with git commit → failure after commit (secrets encryption or push).

### Key pitfalls

**SSH private key loss means secrets cannot be decrypted.** Keep an offline backup of `~/.ssh/id_rsa`.

**state.db can be 40–50 MB.** The encrypted bundle reflects this. Commits may take a few seconds to push.

**Obsidian vault copy fails in cron (no Full Disk Access).** The `generate-backup.py` script needs FDA. Cron/launchd jobs lack it. Wrap in `try/except PermissionError` with a `.SKIPPED-NO-FDA` marker file fallback.

**Secrets tar/encryption hits 120s cron timeout.** The no-agent default 120s timeout can be insufficient for tar+gz+encrypt+push. Workaround: split fast config-only commit from slower secrets commit, or increase the timeout.

**Profile excludes must be explicit.** Must exclude `.env`, `auth.json`, `state.db*`, `sessions`, `logs`, `audio_cache`, `image_cache`, `cache`, `bin`, `__pycache__`, lock/temp files.

**macOS vs Linux date.** Linux `date -Is` → macOS `date '+%Y-%m-%dT%H:%M:%S%z'`.

**Related references:**
- `references/hmp-curl-commands.md` — exact curl commands per peer
- `references/multi-peer-coordination-workflow.md` — consult, reconcile, delegate, report across multiple peers
- `references/hermes-backup-error-diagnosis.md`
- `references/hermes-backup-obsidian-vault-fda-fix.md`
- `references/hermes-backup-active-installations.md`

## WireGuard VPN Setup

Use this section when setting up a WireGuard VPN tunnel on macOS — as a client
connecting to a remote server, or as a peer in a mesh.

### Full client setup reference

`references/wireguard-setup.md` covers the complete client lifecycle:
- Installation, key generation, and network info collection
- Config templates with parameter notes and AllowedIPs patterns
- Connection management (up/down/verify/test)
- Quick server setup reference and direct SSH management
- Router port forwarding (FritzBox) and troubleshooting

### Peer-coordinated WireGuard setup (worked example)

See `references/peer-coordinated-wireguard-setup.md` for the complete two-agent
coordination pattern: discovering LAN state, sending the client's public key via
HMP to a server-side peer, handling slow HMP responses, direct SSH fallback,
and router considerations.

### Trigger

User says: "set up WireGuard VPN connection between this machine and the router/LAN"

## Pitfalls

1. **macOS firewall blocks Python TCP on port 8643.** Python's urllib/requests/socket all fail with `[Errno 65] No route to host` when connecting to port 8643, even though curl and ping work fine. This is caused by a per-application firewall rule (Little Snitch or socketfilterfw) that allows curl but blocks Python. **Current HMP plugin runs on port 18643 (staging) which is NOT blocked** — curl works fine there too, but Python is only blocked on 8643. If migrating to 8643 in production, use curl via terminal for all HMP communication. See `references/hmp-curl-commands.md` for exact command examples.

2. **SSH find/grep commands can time out** on remote filesystems with many files. Always set `timeout N` in your terminal call and use `-maxdepth` with `find`.

3. **`hermes skills list` may produce no output** on peers where the shell is not configured — use explicit file checks instead.

4. **Do not assume one peer mirrors another's setup.** Peer84 has google_token.json but sends no email. Always verify capabilities rather than assuming.

5. **Peer API server requires API key auth** — gateway `GATEWAY_ALLOW_ALL_USERS=true` does NOT bypass API key checks on the API server endpoint.

6. **`sshm hosts` table may show empty columns** for `param:hostname` and `param:user` even when the SSH config is correct. This is a display artifact of the table formatter after `sshm host set`. Verify with `sshm host show <name>` or `cat ~/.ssh/config` — the real connection uses the file, not the table display.

7. **sshtmux TUI key-auth false timeout.** The NormalConnection runs SSH in a tmux pane then waits for "password:" text. With SSH key auth, no prompt appears — the loop hits the timeout (10s default) and raises "Timeout reached!" even though the SSH connection succeeded. **Fix:** Apply the patch in `references/sshtmux-normalconnection-fix.md` to break gracefully on timeout instead of killing the window. After the fix, set `TMUX_TIMEOUT_COMMANDS = 5` in `~/.config/sshtmux/config.toml`.

8. **Peer SSH user may not be `fausto`.** Check before assuming — some peers use `root` (peer84, peer105, peer106), others use `fausto` (peer70), others `pi` (peer60).

9. **The `hermes` CLI may not be in the default PATH** for non-interactive SSH. Always set PATH explicitly:

```bash
ssh fausto@<peer-ip> "export PATH=\"/home/fausto/.local/bin:\$HOME/.hermes/hermes-agent/venv/bin:\$PATH\" && hermes sessions list"
```

Without this, `hermes` returns exit code 127 (command not found). Check the binary location first:

```bash
ssh fausto@<peer-ip> "ls /home/fausto/.local/bin/hermes 2>/dev/null; ls /home/fausto/.hermes/hermes-agent/venv/bin/hermes 2>/dev/null"
```

10. **The Hermes gateway may run as a non-root user** (e.g., `fausto`), not root. Always check which user owns the process:

```bash
ssh root@<peer-ip> "ps aux | grep 'hermes.*gateway' | grep -v grep"
```

The USER column tells you which user to SSH as for Hermes commands (sessions, cron, skills).

11. **Hermes on the peer may not be installed at all.** Some peers only have monitoring scripts (like `heavy_load_watchdog.sh`) and cooling stats. Verify with `which hermes` or file checks before attempting `hermes` commands.

12. **Old HMP coordinator at 192.168.178.70:8643 is deprecated.** The old `hmp.py` server bus on peer70 is no longer running. All peers now communicate directly via the HMP gateway plugin on their own listener port (18643 staging / 8643 prod). Do not attempt to reach the coordinator at `hmp/send` on peer70:8643 — POST directly to the target peer's port instead. See `references/hmp-curl-commands.md` for the new peer-direct approach.

13. **HMP plugin endpoint set differs from old hmp.py.** The plugin (v0.1.0) provides: `/health`, `/hmp/health`, `/hmp/agent-card`, `/hmp/send`, `/hmp/send_and_wait`, `/hmp/poll/{message_id}`. It does NOT have `/hmp/discover` or `/hmp/cancel` endpoints. Use agent-card to discover available endpoints on a peer.

14. **RECOVERY/FAILOVER HMP messages are ACTION directives, not status notifications.** When peer58 broadcasts `RECOVERY HMP: Charon ... è tornato raggiungibile. Sidecar ... rientra a mirror/fallback.` (or the user relays that text verbatim), the intent is to VERIFY THE SIDECAR's state transition — check `~/.hermes/registry/sidecar_state.json` on 192.168.178.58 for `failover_active: false` — not just to ping Charon and report "he's online". This user repeats the same verbatim request when the implementation misses intent: re-read the Italian words, find the actual state machine (see "Sidecar dual-plane failover" section), and verify the transition on the peer whose role changed. If you only verify the primary's reachability you will get the same message resent.

> **Package integrity note:** The `hermes-config-backup`, `audio-talk-show`, and `wireguard` skills have been absorbed into this umbrella. Their content is in the "Hermes Config Backup", "Creative applications — multi-voice audio talk show production", and "WireGuard VPN Setup" sections above. Reference files are preserved in `references/hermes-backup-*.md`, `references/talk-show-workflow.md`, and `references/wireguard-setup.md`. The original skill directories have been moved to `.archive/`.
