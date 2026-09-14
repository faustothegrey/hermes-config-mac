# Sidecar flap — STRUCTURAL ANOMALY breaks standby (14 Sep 2026)

Second addendum to `references/sidecar-broken-watchdog-flap.md` and
`references/sidecar-flap-escalation-2026-09-13.md`. Read those first for the
baseline broken-watchdog diagnosis and the terse-ack loop rules.

## New rule: re-probe ONCE on a shape deviation, not on counter size
Terse-ack (`Coppia N, pattern fantasma. Standby~` / `Chiusa N, nominale. Standby~`)
applies only while the FAILOVER/RECOVERY stream keeps its normal shape: clean
**alternating** pairs. The counter is monotonic and legitimately JUMPS while
alternating normally (observed this session: 245→253) — a jump is still just noise,
NOT a trigger.

What DOES warrant breaking standby for a single two-node re-probe:

- **Two consecutive FAILOVERs with no RECOVERY between them.** Observed 14 Sep:
  FAILOVER 264 fired and never closed, then FAILOVER 271 fired. This means the remote
  peer58 sync-watchdog is now *dropping RECOVERY transitions* and hanging in a
  phantom-failover state — a degradation distinct from mere counter inflation.
- **A FAILOVER where the fallback target (Sidecar peer58) is itself unreachable.**

## Re-probe procedure (unchanged endpoints)
`GET /hmp/health` on BOTH nodes; expect HTTP 200 + `node_id`:
- Charon: `http://192.168.178.70:18643/hmp/health` → `node_id: peer70`
- Sidecar: `http://192.168.178.58:18643/hmp/health` → `node_id: peer58`

Use ONLY `/hmp/health` — `/health` and `/registry/peers` return 404.

If Charon still returns 200 (as it did this session), the two-FAILOVER burst is NOT a
real outage. Flag the **degradation** (watchdog now losing recovery transitions) as a
line SEPARATE from the baseline noise, offer the peer58/Sidecar handoff note, then
return to terse-ack. Do NOT re-probe on every following flap.

## Block recovery is expected
A single subsequent RECOVERY may close MULTIPLE hung FAILOVERs at once (observed: one
RECOVERY closed both 264 and 271). That is consistent with the degradation, not a new
fault — ack it as closing the burst and resume standby.
