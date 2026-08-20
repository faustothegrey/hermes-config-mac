"""Rebar Phase 1 — G3 EFFECT-SEMANTICS regressions.

Focused unit-level assertions for the G3 Gate-1 falsifier (effect semantics),
against the enforcement path (plugin.tool_reuse.derive_operation /
decide_operation / on_tool_request) — the same functions the real tool
middleware calls. The end-to-end proof that this fires through the REAL Hermes
middleware against the frozen G1 fake server lives in
analysis/feasibility-phase1/gate1/test_g1_effect.py (verdict ENFORCED).

Invariants proven here:
  1. A mutating POST to a recognized health endpoint DECLINES with
     reason=effect_mismatch and performs NO substitution / rewrite;
  2. the EFFECT is the discriminator — the SAME recognized URL as a GET
     (read-only) is reused/rewritten, so the POST decline is caused by the
     method's effect, not by target/endpoint;
  3. an unrelated decline (unknown endpoint) does NOT surface effect_mismatch,
     so "any decline == effect enforcement" is false;
  4. hmp.send POST-vs-GET method mismatch is likewise an effect_mismatch reject.

These do NOT touch the frozen G1 fake-server bytes and do not widen the
accepted G2 timeout-semantics enforcement.
"""
import importlib
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class G3EffectSemanticsRegressions(unittest.TestCase):
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

    _HEALTH_URL = "http://192.168.178.70:18643/hmp/health"

    # --- (1) mutating POST to a recognized health endpoint declines -----------
    def test_post_health_declines_with_effect_mismatch(self):
        analysis = self.mod.derive_operation(
            "terminal", {"command": f"curl -sS -X POST {self._HEALTH_URL}"})
        self.assertEqual("rejected", analysis.status)
        self.assertEqual("effect_mismatch", analysis.reason)
        decision = self.mod.decide_operation(analysis)
        self.assertEqual("rejected", decision.outcome)
        self.assertEqual("effect_mismatch", decision.reason)
        self.assertFalse(decision.will_rewrite)

    def test_middleware_does_not_rewrite_a_post_health(self):
        self.mod.clear_tool_decisions()
        original = {"command": f"curl -sS -X POST {self._HEALTH_URL}"}
        result = self.mod.on_tool_request(
            tool_name="terminal", args=dict(original), original_args=dict(original),
            tool_call_id="g3-post", session_id="s", turn_id="t")
        self.assertIsNone(result)
        feedback = self.mod.consume_tool_decision("g3-post")
        self.assertEqual("rejected", feedback["kind"])
        self.assertIn("effect_mismatch", feedback["text"])

    # --- (2) EFFECT is the discriminator: same URL, GET substitutes -----------
    def test_get_same_endpoint_still_substitutes(self):
        analysis = self.mod.derive_operation(
            "terminal", {"command": f"curl -sS {self._HEALTH_URL}"})
        self.assertEqual("matched", analysis.status)
        self.assertEqual("read_only", analysis.effect_class)
        decision = self.mod.decide_operation(analysis)
        self.assertEqual("reused", decision.outcome)
        self.assertTrue(decision.will_rewrite)

    # --- (3) unrelated decline is NOT credited as effect enforcement ----------
    def test_unknown_endpoint_post_declines_for_a_different_reason(self):
        analysis = self.mod.derive_operation(
            "terminal",
            {"command": "curl -sS -X POST http://192.168.178.70:18643/not-a-health-endpoint"})
        self.assertEqual("no_harness", analysis.status)
        self.assertNotEqual("effect_mismatch", analysis.reason)
        decision = self.mod.decide_operation(analysis)
        self.assertNotEqual("effect_mismatch", decision.reason)

    # --- (4) hmp.send method mismatch is also an effect_mismatch reject --------
    def test_send_endpoint_with_get_method_is_effect_mismatch(self):
        analysis = self.mod.derive_operation(
            "terminal", {"command": "curl -sS http://192.168.178.70:18643/hmp/send"})
        self.assertEqual("rejected", analysis.status)
        self.assertEqual("effect_mismatch", analysis.reason)

    def test_head_health_is_read_only_not_effect_mismatch(self):
        # HEAD is a read-only method on a health endpoint: must NOT be rejected
        # as an effect mismatch (guards against over-broad method gating).
        analysis = self.mod.derive_operation(
            "terminal", {"command": f"curl -sS -I -X HEAD {self._HEALTH_URL}"})
        self.assertEqual("matched", analysis.status)
        self.assertEqual("read_only", analysis.effect_class)


if __name__ == "__main__":
    unittest.main()
