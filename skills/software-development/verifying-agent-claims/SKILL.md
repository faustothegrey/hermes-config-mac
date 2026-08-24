---
name: verifying-agent-claims
type: custom
version: 1.0.0
description: "Independently verify another agent's self-reported results."
---

# Verifying Agent Claims — independent reviewer discipline

Use whenever you are the **reviewer / verifier** of work someone else *reports* as done:
a peer agent over HMP, a delegated subagent's final summary, a CI result, a human's
"it's fixed", or a review loop where a developer node posts a step for your verdict.

**Core principle:** a self-report is a claim, not a fact. "Tests pass", "checksums match",
"uploaded successfully", "feature-set identical, no regression" are all *claims to be
checked*, not results to be accepted. Your entire value as reviewer is that you reproduce
the evidence yourself. A verdict issued without independent reproduction is worthless — worse
than none, because it launders unverified confidence as validation.

## When to use

- You must issue a review verdict (ACCEPT / REWORK / REJECT) on another party's deliverable.
- A subagent / peer / tool reports success with external side effects (files written,
  artifacts pushed, services deployed, messages delivered).
- A checksum, hash, version, or "identical to baseline" claim gates a decision.
- A test/battery "N/N PASS" is offered as evidence.
- You are running the reviewer side of a code-review loop (see the HMP loop reference).

## The verification checklist

1. **Verify every checksum/hash/version claim yourself.** Run `sha256sum` / `shasum -a 256`
   on the actual files — locally AND on the remote (`ssh user@host 'sha256sum <path>'`).
   - A *differing* hash paired with "trust me, the feature set is identical" is the single
     most common thing review exists to catch. Either obtain the named baseline artifact and
     produce a real line-level diff, or explicitly downgrade the verdict wording to
     "accepted on PRESENCE evidence (feature markers confirmed present), NOT on a baseline
     diff" and log that limitation. Never let "differs but fine" pass silently.
   - Filename + size + a claimed version are NOT verification. Grep the internal version
     markers from inside the artifact; a zip named vX can declare vY internally.

2. **Reproduce every execution/test claim.** Re-run the battery/tests yourself; never certify
   a PASS you did not personally observe.
   - ⚠️ **Interpreter/venv trap:** run with the *correct* environment (e.g. the project's
     gateway venv `.../hermes-agent/venv/bin/python`), not a bare system `python3`. The wrong
     interpreter can print "Ran 0 tests" or "ModuleNotFoundError" and be misread as failure.
   - ⚠️ **Harness vs discovery:** a file with few `def test_` methods may still be a custom
     `__main__` harness running many sub-assertions (e.g. "30 PASS / 0 FAIL"). `grep -cE
     'def test_'` undercounts it — run the file the way it's meant to run before judging.

3. **Inspect the real artifact, not the description.** For source-review claims, open the
   file and confirm the asserted markers by line number, not from the summary.

4. **Parse the live evidence independently, and hunt for what the report OMITTED.** When the
   claim cites live logs/event streams/counts, parse the raw source yourself. Actively look
   for omissions: duplicate records from a *second* surface, conflicting classifications for
   the same id, empty required fields, off-by-one counts. A real defect often lives in a
   *neighboring* component, not the deliverable under review — in which case ACCEPT the step
   AND raise the finding as a mandatory follow-up fix; state both plainly.

5. **Never fabricate or assume.** If you cannot verify a claim (baseline file absent, remote
   unreachable, evidence missing), say so **explicitly in the verdict**. Honest "could not
   verify X" always beats a confident certification you didn't earn.

## Governance

- 🔴 **Developer ≠ reviewer is a hard rule.** Never independently "review" code you authored —
  self-review is not independent and any ACCEPT it produces is hollow. If you're asked to
  review your own work, refuse and escalate the role assignment to the human owner.
- **Log the verdict to the durable record** (ledger/report), but treat the primary channel
  message (or the reviewed artifact hash) as the authoritative artifact.
- **Keep accepted artifacts FROZEN.** Once an artifact/semantics is accepted, any later change
  to it is a NEW review item, never silent scope-widening.
- **Don't manufacture scope.** If the next "gate/step" isn't actually predeclared anywhere,
  don't invent one to keep busy — park at a clean checkpoint and get the owner's call.

## Handover / push, checksum-verified

When you transfer artifacts to another node as part of the loop:
1. Build a `SHA256SUMS` manifest of exactly the files being sent (exclude `__pycache__`/`*.pyc`).
2. `rsync -az --exclude=__pycache__` them. Use **literal remote paths** (`/home/user/...`) —
   `~` inside an `ssh 'cmd'` expands to the LOCAL home and writes to the wrong place / fails.
3. **Re-hash on the remote and diff against the manifest** before saying "pushed". Only a
   remote-side hash match justifies the word "verified".
4. For a plugin handover, include the package `__init__.py` (the middleware/registration
   entry) — omitting it leaves the remote runtime silently missing the wiring.

## References

- `references/hmp-peer-review-loop-2026-08-23.md` — running a 2h/2h peer-to-peer review loop
  over HMP (send/poll, 2048-byte cap, read verdicts from `messages.db` not logs, both-sides
  cron automation), with the G0-1/G0-2 review worked example including the dual-emit-surface
  finding pattern.

## Related / overlap

- `software-development/loop-coding-guidelines` (user-owned) documents the ABANDONED email
  transport for the same review loop; its transport is dead (replaced by HMP) but its
  reviewer-interpretation guardrails overlap this skill. If the user adopts it for curation,
  consider consolidating the reviewer-discipline parts here.
