---
name: hmp-alert-acknowledgements
description: Use for HMP incident alert acknowledgment.
---

# HMP Alert Acknowledgements

Use this skill for operational alerts received over HMP that explicitly report a Charon/Sidecar FAILOVER or RECOVERY.

## Objective

Acknowledge the stated operational transition without investigation, automation, commentary, or decorative tone. These acknowledgements are intended to be copied/read as compact incident-log lines.

## Procedure

1. Treat the incoming alert as the authoritative source for the counter, address, port, and state.
2. Reply with exactly one Italian line.
3. For **FAILOVER**, include only the failure counter and the temporary registry endpoint:
   - `FAILOVER <counter> — registry temporaneo: <ip>:<port>`
4. For **RECOVERY**, include only Charon reachability and Sidecar mirror/fallback state:
   - `RECOVERY — Charon <ip> raggiungibile; Sidecar <ip> mirror/fallback.`
5. Do not add analysis, hypotheses, troubleshooting, status checks, emojis, greetings, confirmations, or next steps.

## Counter handling

- Preserve the counter value supplied by the alert even if the metric label changes (for example, `registry sync` versus `heartbeat`).
- Do not infer a missing counter or compare it to prior incidents.

## Scope and safety

- This is an acknowledgement workflow, not an authorization to change registry routing, run probes, restart services, or notify other channels.
- If the alert does not give the data needed for its corresponding template, ask one concise question rather than fabricate it.

## Reference

- Session-specific examples and rationale: `references/peer58-charon-sidecar.md`.
