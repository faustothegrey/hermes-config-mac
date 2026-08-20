"""Rebar Phase 1 — G4 DUPLICATE-SAFETY (idempotency) regressions.

Focused unit-level assertions for the G4 Gate-1 falsifier (duplicate-safety /
idempotency semantics), against the enforcement path (plugin.tool_reuse.
derive_operation / decide_operation / on_tool_request) — the same functions the
real tool middleware calls. The end-to-end proof that this fires through the REAL
Hermes middleware against the frozen G1 fake server lives in
analysis/feasibility-phase1/gate1/test_g1_duplicate.py (verdict ENFORCED).

Invariants proven here:
  1. A non-idempotent consume (GET /messages/next) DECLINES with
     reason=idempotency_mismatch and performs NO substitution / rewrite;
  2. IDEMPOTENCY is the discriminator — an idempotent GET /health on the SAME
     host/method-class is reused/rewritten, so the consume decline is caused by
     the operation's idempotency, not by target/host/method;
  3. an unrelated decline (unknown endpoint) does NOT surface
     idempotency_mismatch, so "any decline == duplicate-safety enforcement" is
     false;
  4. the accepted G2 timeout-semantics and G3 effect-semantics declines are
     UNCHANGED (no regression / no scope-widening of the earlier enforcement).

These do NOT touch the frozen G1 fake-server bytes and do not widen the accepted
G2 timeout-semantics / G3 effect-semantics enforcement.
"""
import importlib
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class G4DuplicateSafetyRegressions(unittest.TestCase):
    def setUp(self):
        os.environ["CAPABILITY_REUSE_PERMISSIONS"] = "hmp.network.read"
        os.environ["CAPABILITY_REUSE_AVAILABLE_CAPABILITIES"] = "hmp_client_installed"
        os.environ["CAPABILITY_REUSE_ACTIVE_CAPABILITIES"] = "hmp-healthcheck"
        os.environ["CAPABILITY_REUSE_TOOL_REUSE_MODE"] = "active"
        self.mod = importlib.import_module("plugin.tool_reuse")

    def tearDown(self):
        for key in (
            "CAPABILITY_REUSE_PERMISSIONS",
            "CAPABILITY_REUSE_AVAILABLE_CAPABILITIES",
            "CAPABILITY_REUSE_ACTIVE_CAPABILITIES",
            "CAPABILITY_REUSE_TOOL_REUSE_MODE",
        ):
            os.environ.pop(key, None)

    _BASE = "http://192.168.178.70:18643"
    _HEALTH_URL = _BASE + "/hmp/health"
    _CONSUME_URL = _BASE + "/messages/next"

    # --- (1) non-idempotent consume declines with idempotency_mismatch --------
    def test_consume_declines_with_idempotency_mismatch(self):
        analysis = self.mod.derive_operation(
            "terminal", {"command": f"curl -sS {self._CONSUME_URL}"})
        self.assertEqual("rejected", analysis.status)
        self.assertEqual("idempotency_mismatch", analysis.reason)
        decision = self.mod.decide_operation(analysis)
        self.assertEqual("rejected", decision.outcome)
        self.assertEqual("idempotency_mismatch", decision.reason)
        self.assertFalse(decision.will_rewrite)

    def test_hmp_prefixed_consume_also_declines(self):
        analysis = self.mod.derive_operation(
            "terminal", {"command": f"curl -sS {self._BASE}/hmp/messages/next"})
        self.assertEqual("rejected", analysis.status)
        self.assertEqual("idempotency_mismatch", analysis.reason)

    def test_middleware_does_not_rewrite_a_consume(self):
        self.mod.clear_tool_decisions()
        original = {"command": f"curl -sS {self._CONSUME_URL}"}
        result = self.mod.on_tool_request(
            tool_name="terminal", args=dict(original), original_args=dict(original),
            tool_call_id="g4-consume", session_id="s", turn_id="t")
        self.assertIsNone(result)
        feedback = self.mod.consume_tool_decision("g4-consume")
        self.assertEqual("rejected", feedback["kind"])
        self.assertIn("idempotency_mismatch", feedback["text"])

    # --- (2) IDEMPOTENCY is the discriminator: idempotent /health substitutes -
    def test_idempotent_health_same_host_still_substitutes(self):
        analysis = self.mod.derive_operation(
            "terminal", {"command": f"curl -sS {self._HEALTH_URL}"})
        self.assertEqual("matched", analysis.status)
        self.assertEqual("read_only", analysis.effect_class)
        decision = self.mod.decide_operation(analysis)
        self.assertEqual("reused", decision.outcome)
        self.assertTrue(decision.will_rewrite)

    # --- (3) unrelated decline is NOT credited as duplicate-safety ------------
    def test_unknown_endpoint_declines_for_a_different_reason(self):
        analysis = self.mod.derive_operation(
            "terminal", {"command": f"curl -sS {self._BASE}/not-a-known-endpoint"})
        self.assertNotEqual("idempotency_mismatch", analysis.reason)
        decision = self.mod.decide_operation(analysis)
        self.assertNotEqual("idempotency_mismatch", decision.reason)

    # --- (4) accepted G2/G3 enforcement remains intact (no regression) --------
    def test_g3_effect_mismatch_still_enforced(self):
        analysis = self.mod.derive_operation(
            "terminal", {"command": f"curl -sS -X POST {self._HEALTH_URL}"})
        self.assertEqual("rejected", analysis.status)
        self.assertEqual("effect_mismatch", analysis.reason)

    def test_g2_timeout_semantics_still_enforced(self):
        analysis = self.mod.derive_operation(
            "terminal", {"command": f"curl -sS --max-time 0.2 {self._HEALTH_URL}"})
        self.assertTrue(analysis.whole_request_deadline)
        # sub-second budget preserved, not truncated to 0
        self.assertEqual(0.2, analysis.inputs.get("timeout_seconds"))
        decision = self.mod.decide_operation(analysis)
        self.assertEqual("rejected", decision.outcome)
        self.assertEqual("timeout_semantics_mismatch", decision.reason)


if __name__ == "__main__":
    unittest.main()
