# Sidecar Dual-Plane Failover — verification detail (peer58 ↔ Charon peer70)

Session detail from 2026-08-13 recovery verification. Charon (peer70, 192.168.178.70)
is the HMP registry primary; Sidecar (peer58, 192.168.178.58) is the automatic
mirror/fallback.

## Sidecar script surface (peer58, `~/.hermes/scripts/`)

| Script | Purpose |
|--------|---------|
| `hmp_sidecar.py` | Heartbeat + registry sync watchdog (the state machine) |
| `hmp_sidecar_heartbeat.sh` | Wrapper → `python3 hmp_sidecar.py heartbeat` |
| `hmp_sidecar_registry_sync.sh` | Wrapper → `python3 hmp_sidecar.py registry_sync` |
| `hmp_dual_plane.py` / `hmp_dual_plane_light.py` | Full/light dual-plane HTTP servers |
| `hmp_sidecar_daily_notify.sh` | Daily notification |

CLI: `hmp_sidecar.py heartbeat|registry_sync` — NO explicit demote command.
Demotion happens automatically inside `heartbeat()` via `demote_if_charon_back()`.

## State file: `~/.hermes/registry/sidecar_state.json`

```json
{
  "failover_active": false,
  "heartbeat_failures": 0,
  "last_error": null,
  "last_heartbeat_ok": "2026-08-13T09:46:16+02:00",
  "last_registry_sync_ok": "2026-08-13T09:40:33+02:00",
  "last_registry_update": null,
  "promoted_at": "2026-08-12T07:54:09+02:00",
  "promotion_reason": null,
  "registry_sync_failures": 0
}
```

Reading: `failover_active: false` = demoted / mirror mode. `promoted_at` staying set
after a recovery is NORMAL — `demote_if_charon_back()` only clears `failover_active`
and `promotion_reason`, not `promoted_at`.

## Peer id → IP mapping (from `hmp_sidecar.py` PEERS dict)

| peer id | IP |
|---------|-----|
| peer70  | 127.0.0.1 (Charon; real IP 192.168.178.70) |
| peer84  | 192.168.178.84 |
| peer105 | 192.168.178.105 |
| peer106 | 192.168.178.106 |
| peer58  | 192.168.178.58 |
| peer136 | 192.168.178.136 (trixie) |
| peer128 | 192.168.178.112 (peer id .128, IP is .112!) |

## Verification procedure that worked (2026-08-13)

1. **Sidecar state first** (the actual answer):
   `ssh fausto@192.168.178.58 "cat ~/.hermes/registry/sidecar_state.json"`
   → `failover_active: false`, `last_heartbeat_ok` recent → demote confirmed.
2. **Charon two-layer health**:
   - Network: `ping -c 3 -W 2 192.168.178.70` → 0% loss, ~2.6ms
   - HMP listener: `curl -s -m 5 http://192.168.178.70:18643/hmp/health`
     → `{"status":"ok","node_id":"peer70","bind":"0.0.0.0:18643"}`
3. **Optional round-trip** (proves message processing, not just listener):
   POST `/hmp/send` with `task_type: ping`, poll `/hmp/poll/{id}` until `completed`
   (~6s). Charon responded: "Sì, Charon online e operativo! ... WireGuard connesso (10.0.0.2, handshake con peer58)".

## What NOT to do (the miss this session documents)

Doing ONLY the Charon checks (step 2-3) and answering "Charon is back, nothing to
restore from my side" misses the intent of the RECOVERY broadcast — the instruction
is about the sidecar's role transition. The user resends the identical verbatim
message when the implementation misses intent. Always check the sidecar state file
to confirm the transition actually happened.
