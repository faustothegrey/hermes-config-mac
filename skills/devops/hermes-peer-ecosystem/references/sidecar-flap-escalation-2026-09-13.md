# Sidecar flap loop — escalate the DECISION, don't ack forever (13 Sep 2026)

Addendum to `references/sidecar-broken-watchdog-flap.md`. This session exposed two
refinements to the anti-noise / terse-ack behavior described there.

## 1. The `registry sync N` counter does NOT always reset daily
The flap reference says N "resets daily to ~3". That is the usual case but not a
rule. On 13 Sep a single session saw N run **continuously 193 → 229** (30+
FAILOVER/RECOVERY pairs) with no reset at all. Takeaway: a high or non-resetting N
is just *more of the same broken peer58 sync-watchdog* — it is NOT evidence of a
worse or genuinely-real Charon outage. Do not re-probe or re-escalate merely because
N is large.

## 2. Terse-ack is finite — the unmade fix decision becomes the stall
Once confirmed broken-watchdog, each further flap gets ONE terse line. But that loop
must not run forever. The real failure mode this session: acking dozens of flaps
while the A/B/C fix decision (receive-side filter / fix-on-peer58 / hand-over) was
never actually made or re-surfaced.

The user's standing preference is that a stall must be surfaced ACTIVELY and never
look like quiet. When the flap has clearly persisted unresolved across a long run,
**the unmade A/B/C decision is itself the stall.** Re-raise A/B/C explicitly to the
user (don't just keep incrementing the terse counter) rather than silently absorbing
flap after flap.

## Correct terse line during the loop
`Ack ★ FAILOVER N. Standby~` (or RECOVERY N) — one line, no re-probe. But break out
of it to re-present A/B/C after the loop has run long enough that the decision is
overdue.
