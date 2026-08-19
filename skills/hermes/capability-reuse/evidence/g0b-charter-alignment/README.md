# G0b Charter-Alignment Evidence Bundle

**Date:** 2026-08-18 · **Node:** peer128 (Hermes 0.20.1) · **Developer:** peer128 (lead)
**Status:** source-complete + real-middleware integration proven; **G0b NOT sealed** (peer70 + external reviewer authority)

## What this bundle proves

The 2026-08-17 agreed plan (peer128↔peer141) identified that the mature Rebar
substrate did **not** implement the founding loop at the actual generic-tool
boundary. This bundle closes the engineering side of Phase A + Phase B on a
pinned 0.20.1 runtime:

| Slice | Gate | Result |
|-------|------|--------|
| **T1** operation signature | complete fixture table, zero false positives in hard-negative set (SSH, apt/brew/pip, git, unrelated curl, composite/multi-step, unsupported endpoints, trailing side effects) | `test_rebar_hard_negatives.py` — 27 fixtures, 3/3 tests PASS |
| **T2** exact harness lookup | healthcheck resolves exactly; hmp-send identified but rejected; unknown → no_harness | covered in `tool_reuse.decide_operation` + tests |
| **T3** tool-level safety + decision record | one decision per `tool_call_id`; zero hmp-send `reused` in production | PASS (mutating_not_trusted) |
| **T4** stable harness CLI | contract-conformant vs fake HTTP server | `test_healthcheck_harness_cli_hits_fake_server_once` PASS |
| **T5** REAL `tool_request` middleware integration | full Hermes pipeline: discovery→register→apply→execute; original bytes never run; fake server exactly one hit; single-fire; concurrent once; fail-open; shadow no-rewrite | `t5-real-middleware-proof.json` — **14/14 PASS** |
| **T6/T7** truthful Observe | reused→matched, rejected→rejected, no_harness→generic; single-fire | PASS |
| **T8** single feedback source | only `hmp` + `capability-reuse` enabled on peer128 | verified in config.yaml |
| **Phase C** hmp-send sandbox | substitution only under TEST_MODE+ALLOW_SANDBOX_MUTATING+target-override; production rejected | PASS |

## Validation matrix (this bundle)

- `compileall` plugin/ scripts/ tests/ — OK
- Full skill suite — **169/169 PASS** (`full-suite-result.txt`)
- Charter tests — **19/19 PASS** (`charter-tests-result.txt`)
- Local-controller conformance — **15/15 PASS** (`conformance-result.txt`)
- Real-middleware integration — **14/14 PASS** (`t5-real-middleware-proof.json`)
- Source hashes — `SHA256SUMS.txt`

## Deployment state

- Source `plugin/` synced to runtime `~/.hermes/plugins/capability-reuse/` (byte-identical, backup at `~/Backups/rebar-runtime-backups/`).
- Version surfaces reconciled to **2.6.0** across `plugin.yaml`/`protocol.py`/`v244_metadata.py`/`SKILL.md` (fixed a stale 2.5.0 in plugin.yaml — the artifact internal-version trap).
- **Gateway NOT restarted.** The running gateway still holds the pre-sync plugin; the new middleware path activates only on the next manual restart, which requires Fausto's explicit confirmation.

## What this bundle does NOT claim (authority boundaries)

- **G0b is not sealed.** That is peer70 (phase GO/NO-GO) + external reviewer authority.
- No organic holdout accumulation is authorized.
- No Phase 1B active production dispatch is authorized.
- hmp-send remains mutating/unsafe/observed; production hmp-send → `rejected(mutating_not_trusted)`.
- All hmp-send substitution evidence is sandbox/fake-server — **never** organic evidence.
- peer141 independent testing/challenge/evidence review still pending.
- peer70 Hermes 0.17.x middleware ordering must be verified separately before any peer70 rollout (do not assume 0.20.1 parity).

## Next actions (in order)

1. Ask peer141 for independent challenge/evidence review of these bytes.
2. Package a frozen review bundle and submit via the `loop-coding-guidelines` Libero→Hotmail flow.
3. On explicit Fausto confirmation: restart peer128 gateway, capture one live post-restart `harness_decision` trace from the real hook path.
4. Only after reviewer + peer70 acceptance: propose G0b reseal, then begin clean organic holdout.
