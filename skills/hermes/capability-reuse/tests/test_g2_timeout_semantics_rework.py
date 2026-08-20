"""Rebar Phase 1 — G2 NARROW/REWORK regressions (timeout semantics).

Proves the reviewer-required remediation for the G2 falsifier
(GATE_VERDICT_LEDGER: ACCEPT + NARROW/REWORK before G3):

  1. whole-request / per-operation MISMATCH declines with NO substitution
     (explicit reason=timeout_semantics_mismatch);
  2. COMPATIBLE timeout semantics can still substitute;
  3. SUB-SECOND budgets survive derivation UNCHANGED (no int(float("0.2"))==0);
  4. existing G1 behaviour remains green (the G1 real-middleware falsifier now
     reports ENFORCED — exercised separately via test_g1_timeout.py).

These are unit-level assertions against the enforcement path
(plugin.tool_reuse.derive_operation / decide_operation), the same functions the
real tool middleware calls. They do NOT touch the frozen G1 fake-server bytes.
"""
import importlib
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class G2TimeoutSemanticsRegressions(unittest.TestCase):
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

    # --- (1) whole-request vs per-op MISMATCH declines, no substitution -------
    def test_whole_request_maxtime_curl_declines_with_timeout_semantics_reason(self):
        analysis = self.mod.derive_operation(
            "terminal", {"command": f"curl -sS --max-time 5 {self._HEALTH_URL}"})
        # still a matched health op (derive must not misclassify)...
        self.assertEqual("matched", analysis.status)
        self.assertEqual("hmp.health", analysis.operation_kind)
        # ...but flagged as a whole-request deadline
        self.assertTrue(analysis.whole_request_deadline)

        decision = self.mod.decide_operation(analysis)
        self.assertEqual("rejected", decision.outcome)
        self.assertEqual("timeout_semantics_mismatch", decision.reason)
        self.assertFalse(decision.will_rewrite)

    def test_short_flag_m_also_declines(self):
        analysis = self.mod.derive_operation(
            "terminal", {"command": f"curl -sS -m 2 {self._HEALTH_URL}"})
        self.assertTrue(analysis.whole_request_deadline)
        decision = self.mod.decide_operation(analysis)
        self.assertEqual("rejected", decision.outcome)
        self.assertEqual("timeout_semantics_mismatch", decision.reason)

    def test_middleware_does_not_rewrite_a_maxtime_curl(self):
        self.mod.clear_tool_decisions()
        original = {"command": f"curl -sS --max-time 0.2 {self._HEALTH_URL}"}
        result = self.mod.on_tool_request(
            tool_name="terminal", args=dict(original), original_args=dict(original),
            tool_call_id="g2-mismatch", session_id="s", turn_id="t")
        # no substitution
        self.assertIsNone(result)
        feedback = self.mod.consume_tool_decision("g2-mismatch")
        self.assertEqual("rejected", feedback["kind"])
        self.assertIn("timeout_semantics_mismatch", feedback["text"])

    # --- (2) COMPATIBLE timeout semantics can STILL substitute ----------------
    def test_curl_without_maxtime_still_substitutes(self):
        analysis = self.mod.derive_operation(
            "terminal", {"command": f"curl -s {self._HEALTH_URL}"})
        self.assertEqual("matched", analysis.status)
        self.assertFalse(analysis.whole_request_deadline)
        decision = self.mod.decide_operation(analysis)
        self.assertEqual("reused", decision.outcome)
        self.assertEqual("harness_reuse", decision.reason)
        self.assertTrue(decision.will_rewrite)

    def test_execute_code_health_without_maxtime_still_substitutes(self):
        analysis = self.mod.derive_operation(
            "execute_code",
            {"code": f"import requests\nrequests.get('{self._HEALTH_URL}', timeout=7)"})
        self.assertEqual("matched", analysis.status)
        self.assertFalse(analysis.whole_request_deadline)
        decision = self.mod.decide_operation(analysis)
        self.assertEqual("reused", decision.outcome)
        self.assertTrue(decision.will_rewrite)

    # --- (3) SUB-SECOND budget survives derivation UNCHANGED ------------------
    def test_subsecond_budget_is_not_truncated_to_zero(self):
        analysis = self.mod.derive_operation(
            "terminal", {"command": f"curl -sS --max-time 0.2 {self._HEALTH_URL}"})
        # the OLD bug: int(float("0.2")) == 0 -> socket timeout 0
        self.assertEqual(0.2, analysis.inputs["timeout_seconds"])
        self.assertNotEqual(0, analysis.inputs["timeout_seconds"])

    def test_fractional_execute_code_budget_preserved(self):
        analysis = self.mod.derive_operation(
            "execute_code",
            {"code": f"import requests\nrequests.get('{self._HEALTH_URL}', timeout=0.5)"})
        self.assertEqual(0.5, analysis.inputs["timeout_seconds"])

    def test_whole_integer_budget_stays_int(self):
        # regression guard: preserving fractional must NOT turn 5 into 5.0 and
        # break existing exact-dict assertions elsewhere in the suite.
        analysis = self.mod.derive_operation(
            "terminal", {"command": f"curl -sS --max-time 5 {self._HEALTH_URL}"})
        self.assertEqual(5, analysis.inputs["timeout_seconds"])
        self.assertIsInstance(analysis.inputs["timeout_seconds"], int)

    def test_invalid_timeout_still_rejected(self):
        analysis = self.mod.derive_operation(
            "terminal", {"command": f"curl -sS --max-time abc {self._HEALTH_URL}"})
        self.assertEqual("rejected", analysis.status)
        self.assertEqual("invalid_timeout", analysis.reason)

    # --- (4) unrelated decline is NOT credited as timeout enforcement ---------
    def test_unsupported_target_declines_for_a_different_reason(self):
        # an unknown host declines, but NOT for timeout_semantics_mismatch —
        # proving "any decline == enforcement" is false.
        analysis = self.mod.derive_operation(
            "terminal", {"command": "curl -sS --max-time 5 http://10.0.0.254:18643/hmp/health"})
        self.assertEqual("rejected", analysis.status)
        decision = self.mod.decide_operation(analysis)
        self.assertNotEqual("timeout_semantics_mismatch", decision.reason)


if __name__ == "__main__":
    unittest.main()
