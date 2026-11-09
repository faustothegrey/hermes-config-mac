# peer58 HMP alert acknowledgements

## Scope
Inbound HMP alert relays from **peer58** about the Charon/Sidecar dual-plane failover loop.

## Observed, accepted response contract
Reply with **exactly one Italian line**, manually; do not add diagnosis, validation, commands, emojis, acknowledgements, or automation proposals.

- On `FAILOVER HMP` with `registry sync N fallimenti` and a temporary registry endpoint:
  `FAILOVER: registry sync N fallimenti; registry temporaneo su Sidecar 192.168.178.58:18643.`
- On `RECOVERY HMP` saying Charon is reachable and Sidecar re-enters fallback:
  `RECOVERY: Charon 192.168.178.70 raggiungibile; Sidecar 192.168.178.58 in mirror/fallback.`

## Example burst
A sequence of counters 945→951, each followed by a recovery broadcast, was handled solely with the corresponding one-line acknowledgement. The counter must be copied exactly from the incoming alert.
