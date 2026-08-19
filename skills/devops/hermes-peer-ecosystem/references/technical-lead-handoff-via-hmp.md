# Cross-peer technical-lead handoff via HMP

Use this when Fausto assigns one peer to lead a multi-peer development effort.

## Coordination sequence

1. Contact the implementation peer directly through its HMP gateway. State that the assignment came directly from Fausto.
2. Request a concrete handoff:
   - current skill and runtime-plugin versions;
   - runtime mode and enabled state;
   - owned/recent artifacts with exact paths and version or commit pointers;
   - blockers and frozen decisions;
   - proposed role under the new lead.
3. Confirm the implementation role, then notify the coordinator/publisher of the proposed governance split. If a normal consultation peer is offline, record that without making it an automatic blocker.
4. Obtain terminal HMP acknowledgements from both peers before reporting that governance is established.
5. Keep technical leadership separate from independent release authority.

## Reusable governance split

- **Technical lead:** direction, integration sequencing, engineering gates, release readiness, and development coordination.
- **Implementation owner + evidence producer:** implementation, hook/integration wiring, validators, analyzers, and raw gate evidence. Producing QA evidence is not the final release verdict.
- **Coordinator / authoritative publisher:** independent phase GO/NO-GO and publishing authority. The lead's gates feed this decision rather than replacing it.

## First handoff check: source/runtime identity

Before commissioning new feature work, compare version identity across the skill, source plugin manifest, runtime plugin manifest, and runtime controller/protocol code. Distinguish a real mismatch from intentional historical comments or compatibility defaults. Ask the implementation peer for the minimal correction, but do not apply it until any restart or configuration side effects are separately authorized. Preserve existing NO-GO and frozen gates throughout the handoff.

## HMP verification pattern

A successful `POST /hmp/send` proves acceptance only. Poll `/hmp/poll/{message_id}` until `completed`, `failed`, or `timed_out`, and capture `response_text`. `delivering` can legitimately persist for around a minute; use bounded repolling instead of sending duplicate requests.

## Worked example: Capability-Reuse/Rebar, 2026-08-17

Fausto assigned peer128 as technical lead. peer141 accepted implementation and evidence ownership; peer70 retained phase GO/NO-GO and authoritative publishing. The first handoff exposed a source/runtime identity mismatch: source manifest and protocol code were 2.6.0 while peer141's runtime manifest remained 2.5.0. The one-line correction was identified but not applied because it implied a gateway restart requiring separate authorization.