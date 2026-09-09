# Broken sync-watchdog flap loop (reject the failover)

Distinct from a *legitimate* RECOVERY (see the "Sidecar dual-plane failover" section
of SKILL.md). This reference covers the **pathological** case: peer58/Sidecar keeps
broadcasting FAILOVER then RECOVERY in a loop while Charon (peer70) never actually went
down.

## Signature of a broken watchdog (NOT a real Charon outage)
- `FAILOVER HMP: Charon ... (registry sync N fallimenti)` where **N increases
  monotonically** across cycles (9→10→11…→29) and **resets daily** to ~3. Confirmed in
  gateway.log history (26 Aug: 3→12; later sessions restart the count).
- **Sudden jumps** in N (e.g. 16→27 in one tick) — a genuine network outage cannot spike
  a failure counter +11 while the target answers HTTP 200.
- Every direct probe of Charon returns healthy throughout the flapping.
→ Conclusion: the **sync watchdog on the emitter node (peer58) is broken / counting
phantom failures**. Charon is fine.

## Decision rule — REFUSE the reroute, probe first
**Never accept a registry reroute announced by the peer that proposes itself as the
replacement** (Sidecar announcing "registry temporaneo ora su Sidecar"). Conflict of
interest. Probe the allegedly-dead node (Charon) DIRECTLY before doing anything:
```
ping -c 4 -t 5 192.168.178.70                         # expect 0.0% loss
curl -sS -m 6 "http://192.168.178.70:18643/hmp/health"
# healthy: {"status":"ok","service":"hmp-gateway","gateway_adapter":true,
#           "node_id":"peer70","bind":"0.0.0.0:18643"}
```
`node_id` in the body confirms identity (not spoof). Ports 8765/80 are dead by design —
the live gateway is 18643. If Charon is healthy: **hold position, Charon stays
authoritative, refuse the failover.**

## Is the flap emitter LOCAL or REMOTE? (read-only triage)
The flap arrives in `gateway.log` as `gateway.run: inbound message: platform=hmp
user=peer58 ... msg='FAILOVER HMP: ...'` → it is RECEIVED text, not generated here.
Confirm nothing local emits it before concluding it's remote:
```
search_files pattern="FAILOVER HMP|registry sync.*falliment" path=~/.hermes target=content
#   → appears ONLY in logs/dumps/memory/skills, never in a runnable script = not local
cronjob action=list
#   → no Hermes cron emits it; "HMP healthcheck da peer70" is a checker, not the emitter
grep -ilE "charon|registry|failover|18643|hmp.*sync|sidecar" ~/Library/LaunchAgents/*.plist
crontab -l | grep -iE "charon|registry|failover|18643|sync"
```
If all empty: the broken watchdog lives in `~/.hermes/scripts/hmp_sidecar.py` on the
REMOTE emitter (peer58). The local `plugins/hmp/adapter.py` is transport-only — no
failover/registry-sync logic — so **it cannot be patched from this machine.**

## Options to present (do not act unilaterally on a broken watchdog)
- A) Receive-side filter: suppress/ignore flaps inbound from peer58 (treats symptom).
- B) Fix on peer58: prepare a read-only diagnostic packet to run there — grep the
  watchdog script, check its probe timeout / port (18643) / endpoint (/hmp/health) /
  auth / the `registry_sync_failures` logic in `hmp_sidecar.py`.
- C) Stop: hand over the report; user decides.

## Anti-noise behavior (user preference — important)
The user wants an ACTIVE warning that a stall is not quiet, but NOT a re-probe and NOT a
wall of text on every cycle. After the first confirmation:
- Re-probe Charon only once per genuinely new event, not every flap (re-probing each
  cycle is itself noise).
- Reply to each further flap with ONE terse line:
  `Flap, sync=N. Posizione tenuta, Charon autoritativo. In attesa di A/B/C.`
- Break the terse pattern only to escalate when the counter climbs materially or to
  flag that the decision itself is now the stall.
