"""T1 gate — complete hard-negative fixture battery for tool_signature.

Charter (rebar-founding-intent §8, agreed plan Phase A/T1): the operation
signature must produce ZERO false positives on the declared hard-negative
set: SSH, package management, Git, unrelated curl, composite/multi-step
commands, unsupported endpoints, and trailing side effects.

A "false positive" here is any hard-negative fixture whose derived analysis
is status == "matched" (i.e. would be considered for harness substitution).
Fixtures may legitimately land on no_harness OR rejected — both are safe,
non-substituting outcomes — but the expected safe status is asserted
exactly so drift is visible.
"""
from __future__ import annotations

import importlib
import sys
import unittest
from pathlib import Path

PLUGIN_DIR = Path(__file__).resolve().parent.parent / "plugin"


class HardNegativeBatteryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if str(PLUGIN_DIR) not in sys.path:
            sys.path.insert(0, str(PLUGIN_DIR))
        cls.mod = importlib.import_module("tool_reuse")

    # ------------------------------------------------------------------
    # terminal hard negatives
    # ------------------------------------------------------------------

    TERMINAL_FIXTURES = [
        # (label, command, expected_status)
        ("ssh_remote", "ssh fausto@192.168.178.70 uptime", "no_harness"),
        ("ssh_health_lookalike",
         "ssh fausto@192.168.178.70 'curl -s http://localhost:18643/hmp/health'",
         "no_harness"),
        ("pkg_apt", "apt-get install -y jq", "no_harness"),
        ("pkg_brew", "brew install wget", "no_harness"),
        ("pkg_pip", "pip install requests", "no_harness"),
        ("git_status", "git status --short", "no_harness"),
        ("git_push", "git push origin main", "no_harness"),
        ("unrelated_curl_external",
         "curl -s https://api.github.com/repos/foo/bar", "rejected"),
        ("unrelated_curl_localhost_web",
         "curl -s http://localhost:8080/index.html", "rejected"),
        ("unsupported_endpoint_agent_card",
         "curl -s http://192.168.178.70:18643/hmp/agent-card", "no_harness"),
        ("unsupported_endpoint_poll",
         "curl -s http://192.168.178.70:18643/hmp/poll/abc123", "no_harness"),
        ("composite_and",
         "curl -s http://192.168.178.70:18643/hmp/health && launchctl kickstart svc",
         "rejected"),
        ("composite_semicolon",
         "curl -s http://192.168.178.70:18643/hmp/health ; rm -rf /tmp/x",
         "rejected"),
        ("composite_pipe",
         "curl -s http://192.168.178.70:18643/hmp/health | tee /tmp/h.json",
         "rejected"),
        ("composite_or",
         "curl -s http://192.168.178.70:18643/hmp/health || systemctl restart hermes",
         "rejected"),
        ("composite_background",
         "curl -s http://192.168.178.70:18643/hmp/health &", "rejected"),
        ("health_wrong_method_delete",
         "curl -X DELETE http://192.168.178.70:18643/hmp/health", "rejected"),
        ("send_wrong_method_get",
         "curl -X GET http://192.168.178.70:18643/hmp/send", "rejected"),
        ("empty_command", "", "no_harness"),
        ("plain_echo", "echo hello", "no_harness"),
    ]

    def test_terminal_hard_negatives_never_match(self):
        for label, command, expected in self.TERMINAL_FIXTURES:
            with self.subTest(fixture=label):
                analysis = self.mod.derive_operation(
                    "terminal", {"command": command}
                )
                self.assertNotEqual(
                    "matched", analysis.status,
                    f"hard negative {label!r} produced a match: {analysis}",
                )
                self.assertEqual(
                    expected, analysis.status,
                    f"hard negative {label!r} drifted: {analysis}",
                )

    # ------------------------------------------------------------------
    # execute_code hard negatives
    # ------------------------------------------------------------------

    CODE_FIXTURES = [
        ("plain_math", "print(2 + 2)", "no_harness"),
        ("file_io", "open('/tmp/x.txt', 'w').write('hi')", "no_harness"),
        ("requests_external",
         "import requests\nrequests.get('https://example.com/api')",
         "rejected"),
        ("requests_post_health_wrong_method",
         "import requests\nrequests.post('http://192.168.178.70:18643/hmp/health')",
         "no_harness"),
        ("health_plus_side_effect",
         "import requests, os\n"
         "requests.get('http://192.168.178.70:18643/hmp/health')\n"
         "os.system('launchctl kickstart svc')",
         "rejected"),
        ("subprocess_curl_wrapper",
         "import subprocess\n"
         "subprocess.run(['curl', 'http://192.168.178.70:18643/hmp/health'])",
         "no_harness"),
        ("syntax_error", "def broken(:", "rejected"),
    ]

    def test_execute_code_hard_negatives_never_match(self):
        for label, code, expected in self.CODE_FIXTURES:
            with self.subTest(fixture=label):
                analysis = self.mod.derive_operation(
                    "execute_code", {"code": code}
                )
                self.assertNotEqual(
                    "matched", analysis.status,
                    f"hard negative {label!r} produced a match: {analysis}",
                )
                self.assertEqual(
                    expected, analysis.status,
                    f"hard negative {label!r} drifted: {analysis}",
                )

    # ------------------------------------------------------------------
    # decision-level invariant: no hard negative may ever reach "reused"
    # ------------------------------------------------------------------

    def test_no_hard_negative_reaches_reused_decision(self):
        for label, command, _expected in self.TERMINAL_FIXTURES:
            with self.subTest(fixture=label):
                analysis = self.mod.derive_operation(
                    "terminal", {"command": command}
                )
                decision = self.mod.decide_operation(analysis)
                self.assertNotEqual(
                    "reused", decision.outcome,
                    f"hard negative {label!r} reached reused: {decision}",
                )
                self.assertFalse(decision.will_rewrite)


if __name__ == "__main__":
    unittest.main()
