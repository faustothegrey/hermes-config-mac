# Peer58 Charon/Sidecar alert convention

## Applies to

Operational HMP notifications naming Charon at `192.168.178.70` and Sidecar at `192.168.178.58`.

## Established acknowledgement forms

- Registry-sync failure example: `FAILOVER 1097 — registry temporaneo: 192.168.178.58:18643`
- Heartbeat failure example: `FAILOVER 3 — registry temporaneo: 192.168.178.58:18643`
- Recovery example: `RECOVERY — Charon 192.168.178.70 raggiungibile; Sidecar 192.168.178.58 mirror/fallback.`

## Notes

Metric labels can differ while the required reply format remains the same: preserve the reported numeric counter and registry endpoint. This reference is illustrative; current alerts remain the source of truth.
