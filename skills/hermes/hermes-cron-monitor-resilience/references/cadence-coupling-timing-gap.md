# Cadence-coupling timing gap (second silent-stall mode)

A failure mode distinct from the rate-limit stall documented in SKILL.md.
Verified 2026-08-21 (peer128) on the Rebar human-mail review loop — "the G4 gap".

## Symptom

- A time-sensitive item became "due" (a queued mail with `send_after 22:22`) but
  was never released.
- The ledger claimed the step was "SENT, awaiting verdict", yet the queue file
  still read `"sent": false` and `state.json` for that step had empty
  `thread_ids` / `reply_ids`. The whole loop looked quiet all night — no error,
  no alert.

## Root cause — pure cadence math, no fault

The send-side scheduler tick (`humanmail.py dispatch`) was invoked ONLY from the
review watchdog's `monitor_script`, which runs every 120m. `dispatch` itself is
self-guarding: it HOLDs outside quiet-hours (08:00–23:00 local) and honours each
mail's randomized `send_after` + hold/gap spacing.

Timeline of the miss:

| Tick (120m) | Item due 22:22? | Inside 08–23? | Result |
|---|---|---|---|
| 20:08 | not yet | yes | nothing to send |
| 22:08 | no — 14 min early | yes | **missed by minutes** |
| 00:08 / 02:08 / 04:08 / 06:08 | yes | no | legitimate HOLD |
| 08:08 (next) | yes | yes | finally sends |

The due moment landed in a dead zone between two coarse ticks, then every later
tick fell outside quiet-hours, so the item slipped past the 23:00 edge to the
next morning. No rate-limit, no paused cron, no rescue needed — just a slow
cadence gated by a time window.

## The rule

**Never couple a time-sensitive release to a slow, agentful, or hash-gated
monitor tick.** Two coarse gates in series (120m cadence × quiet-hours window)
multiply into large, silent latency.

Give the time-sensitive action its OWN dedicated `no_agent` cron at a cadence
fine enough to bound the wait (e.g. every 15m). Let the underlying command keep
self-guarding (quiet-hours, `send_after`, spacing) — polling it often is safe
because it only releases once its own `send_after` has arrived. A due item then
waits at most the fine period instead of the monitor's period, and cannot be
lost to the quiet-hour edge. The slow monitor may still call the same command
too — harmless redundant coverage; it stays the review / reply-pickup path.

## Implementation applied (peer128)

- `~/.hermes/scripts/human-mail-dispatch.sh` — calls only `humanmail.py dispatch`,
  logs to the shared side log, silent on success (`no_agent` watchdog pattern).
- Cron `human-mail-dispatch` (`a9e7580b6f61`, `no_agent`, every 15m,
  deliver=local), decoupled from `watchdog-libero-mail-review` (`5a94532c1745`,
  every 120m).
- Verified: running `dispatch` at 06:39 (outside quiet-hours) correctly printed
  `HOLD: outside quiet hours (08:00-23:00 local); 1 queued` — proving the fine
  cron won't send robotically off-hours.

## Ledger-honesty corollary

Mark a step "SENT" only after the queue/state confirms an ACTUAL dispatch
(`"sent": true`, non-empty `thread_ids`), never at enqueue time. Enqueued ≠ sent.
Conflating the two is what let this stall masquerade as "awaiting verdict" for
hours. When auditing a loop, treat the queue/state file as source of truth over
any human-written ledger.
