import importlib
import json
import os
import stat
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class ToolOperationSignatureTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        os.environ["CAPABILITY_REUSE_HARNESS_INPUT_DIR"] = self._tmp.name
        os.environ["CAPABILITY_REUSE_PERMISSIONS"] = "hmp.network.read"
        os.environ["CAPABILITY_REUSE_AVAILABLE_CAPABILITIES"] = "hmp_client_installed"
        os.environ["CAPABILITY_REUSE_ACTIVE_CAPABILITIES"] = "hmp-healthcheck"

    def tearDown(self):
        for key in (
            "CAPABILITY_REUSE_PERMISSIONS",
            "CAPABILITY_REUSE_AVAILABLE_CAPABILITIES",
            "CAPABILITY_REUSE_ACTIVE_CAPABILITIES",
            "CAPABILITY_REUSE_TOOL_REUSE_MODE",
            "CAPABILITY_REUSE_HARNESS_INPUT_DIR",
            "CAPABILITY_REUSE_TEST_MODE",
            "CAPABILITY_REUSE_ALLOW_SANDBOX_MUTATING",
            "HMP_SEND_TARGET_OVERRIDE",
        ):
            os.environ.pop(key, None)
        self._tmp.cleanup()

    def _module(self):
        try:
            return importlib.import_module("plugin.tool_reuse")
        except ModuleNotFoundError:
            self.fail("plugin.tool_reuse is missing")

    def test_terminal_hmp_health_curl_derives_exact_operation(self):
        mod = self._module()
        analysis = mod.derive_operation(
            "terminal",
            {"command": "curl -sS --max-time 5 http://192.168.178.70:18643/hmp/health"},
        )

        self.assertEqual("matched", analysis.status)
        self.assertEqual("hmp.health", analysis.operation_kind)
        self.assertEqual("read_only", analysis.effect_class)
        self.assertEqual("peer70", analysis.target)
        self.assertEqual({"peer_list": ["peer70"], "timeout_seconds": 5}, analysis.inputs)

    def test_composite_health_command_is_rejected_as_partial_coverage(self):
        mod = self._module()
        analysis = mod.derive_operation(
            "terminal",
            {"command": "curl -s http://192.168.178.70:18643/hmp/health && launchctl kickstart service"},
        )

        self.assertEqual("rejected", analysis.status)
        self.assertEqual("partial_coverage", analysis.reason)

    def test_unrelated_terminal_command_reports_no_harness(self):
        mod = self._module()
        analysis = mod.derive_operation("terminal", {"command": "git status --short"})

        self.assertEqual("no_harness", analysis.status)
        self.assertEqual("unrecognized_operation", analysis.reason)

    def test_execute_code_requests_health_derives_operation(self):
        mod = self._module()
        analysis = mod.derive_operation(
            "execute_code",
            {"code": "import requests\nrequests.get('http://192.168.178.70:18643/hmp/health', timeout=7)"},
        )

        self.assertEqual("matched", analysis.status)
        self.assertEqual("hmp.health", analysis.operation_kind)
        self.assertEqual({"peer_list": ["peer70"], "timeout_seconds": 7}, analysis.inputs)

    def test_execute_code_with_extra_effect_is_rejected_as_partial_coverage(self):
        mod = self._module()
        analysis = mod.derive_operation(
            "execute_code",
            {
                "code": (
                    "import requests, os\n"
                    "requests.get('http://192.168.178.70:18643/hmp/health')\n"
                    "os.system('launchctl kickstart service')"
                )
            },
        )

        self.assertEqual("rejected", analysis.status)
        self.assertEqual("partial_coverage", analysis.reason)

    def test_terminal_hmp_send_curl_extracts_normalized_inputs(self):
        mod = self._module()
        command = (
            "curl -sS -X POST http://192.168.178.141:18643/hmp/send "
            "-H 'Content-Type: application/json' "
            "-d '{\"to_peer\":\"peer141\",\"text\":\"hello\",\"session_id\":\"s1\"}'"
        )
        analysis = mod.derive_operation("terminal", {"command": command})

        self.assertEqual("matched", analysis.status)
        self.assertEqual("hmp.send", analysis.operation_kind)
        self.assertEqual("mutating", analysis.effect_class)
        self.assertEqual("peer141", analysis.target)
        self.assertEqual(
            {"peer": "peer141", "text": "hello", "session_id": "s1"},
            analysis.inputs,
        )

    def test_healthcheck_is_selected_only_in_active_tool_reuse_mode(self):
        mod = self._module()
        analysis = mod.derive_operation(
            "terminal",
            {"command": "curl -s http://192.168.178.70:18643/hmp/health"},
        )

        shadow = mod.decide_operation(analysis)
        self.assertEqual("rejected", shadow.outcome)
        self.assertEqual("shadow_mode", shadow.reason)
        self.assertFalse(shadow.will_rewrite)

        os.environ["CAPABILITY_REUSE_TOOL_REUSE_MODE"] = "active"
        active = mod.decide_operation(analysis)
        self.assertEqual("reused", active.outcome)
        self.assertEqual("hmp-healthcheck", active.capability_id)
        self.assertEqual("1.0.0", active.capability_version)
        self.assertTrue(active.will_rewrite)

    def test_hmp_send_is_rejected_in_production_as_mutating_not_trusted(self):
        mod = self._module()
        os.environ["CAPABILITY_REUSE_TOOL_REUSE_MODE"] = "active"
        analysis = mod.derive_operation(
            "terminal",
            {
                "command": (
                    "curl -sS -X POST http://192.168.178.141:18643/hmp/send "
                    "-H 'Content-Type: application/json' -d '{\"to_peer\":\"peer141\",\"text\":\"hello\"}'"
                )
            },
        )

        decision = mod.decide_operation(analysis)

        self.assertEqual("rejected", decision.outcome)
        self.assertEqual("mutating_not_trusted", decision.reason)
        self.assertFalse(decision.will_rewrite)

    def test_tool_request_middleware_rewrites_only_command_and_records_audit_trace(self):
        mod = self._module()
        os.environ["CAPABILITY_REUSE_TOOL_REUSE_MODE"] = "active"
        original = {
            "command": "curl -s http://192.168.178.70:18643/hmp/health",
            "timeout": 17,
            "workdir": "/tmp",
            "background": False,
        }

        result = mod.on_tool_request(
            tool_name="terminal",
            args=dict(original),
            original_args=dict(original),
            tool_call_id="tool-health-1",
            session_id="session-1",
            turn_id="turn-1",
        )

        self.assertEqual(17, result["args"]["timeout"])
        self.assertEqual("/tmp", result["args"]["workdir"])
        self.assertFalse(result["args"]["background"])
        self.assertNotEqual(original["command"], result["args"]["command"])
        self.assertIn("harness_cli.py", result["args"]["command"])
        self.assertIn("hmp-healthcheck", result["args"]["command"])
        self.assertEqual("capability-reuse", result["source"])
        self.assertEqual("harness_reuse", result["reason"])
        self.assertEqual("hmp-healthcheck@1.0.0", result["name"])

        payload_files = list(Path(self._tmp.name).glob("*.json"))
        self.assertEqual(1, len(payload_files))
        self.assertEqual(
            {"peer_list": ["peer70"], "timeout_seconds": 5},
            json.loads(payload_files[0].read_text()),
        )
        self.assertEqual(0o600, stat.S_IMODE(payload_files[0].stat().st_mode))

    def test_tool_decision_feedback_is_truthful_and_single_fire(self):
        mod = self._module()
        mod.clear_tool_decisions()
        original = {"command": "git status --short"}
        self.assertIsNone(mod.on_tool_request(
            tool_name="terminal",
            args=dict(original),
            original_args=dict(original),
            tool_call_id="tool-generic-1",
        ))

        feedback = mod.consume_tool_decision("tool-generic-1")
        self.assertEqual("generic", feedback["kind"])
        self.assertIn("no specialized harness", feedback["text"])
        self.assertIsNone(mod.consume_tool_decision("tool-generic-1"))

    def test_consuming_decision_emits_one_correlated_harness_decision_event(self):
        mod = self._module()
        mod.clear_tool_decisions()
        captured = []
        original_emitter = mod.events.emit_harness_decision
        mod.events.emit_harness_decision = lambda **kwargs: captured.append(kwargs) or "event-1"
        try:
            mod.on_tool_request(
                tool_name="terminal",
                args={"command": "git status --short"},
                original_args={"command": "git status --short"},
                tool_call_id="tool-event-1",
                session_id="session-event",
                turn_id="turn-event",
                task_id="task-event",
            )
            self.assertIsNotNone(mod.consume_tool_decision("tool-event-1"))
            self.assertIsNone(mod.consume_tool_decision("tool-event-1"))
        finally:
            mod.events.emit_harness_decision = original_emitter

        self.assertEqual(1, len(captured))
        self.assertEqual("tool-event-1", captured[0]["tool_call_id"])
        self.assertEqual("no_harness", captured[0]["outcome"])
        self.assertEqual("session-event", captured[0]["context"]["session_id"])

    def test_production_hmp_send_is_never_rewritten(self):
        mod = self._module()
        mod.clear_tool_decisions()
        os.environ["CAPABILITY_REUSE_TOOL_REUSE_MODE"] = "active"
        original = {
            "command": (
                "curl -sS -X POST http://192.168.178.141:18643/hmp/send "
                "-H 'Content-Type: application/json' -d '{\"to_peer\":\"peer141\",\"text\":\"hello\"}'"
            )
        }

        result = mod.on_tool_request(
            tool_name="terminal",
            args=dict(original),
            original_args=dict(original),
            tool_call_id="tool-send-prod",
        )

        self.assertIsNone(result)
        feedback = mod.consume_tool_decision("tool-send-prod")
        self.assertEqual("rejected", feedback["kind"])
        self.assertIn("mutating_not_trusted", feedback["text"])

    def test_plugin_registers_tool_request_middleware(self):
        plugin = importlib.reload(importlib.import_module("plugin"))

        class FakeCtx:
            def __init__(self):
                self.hooks = []
                self.middleware = []

            def register_hook(self, name, callback):
                self.hooks.append((name, callback))

            def register_middleware(self, kind, callback):
                self.middleware.append((kind, callback))

            def register_tool(self, **kwargs):
                pass

        ctx = FakeCtx()
        plugin.register(ctx)

        self.assertEqual([("tool_request", plugin.on_tool_request)], ctx.middleware)

    def test_pre_tool_hook_prefers_tool_specific_decision_and_single_fires(self):
        mod = self._module()
        plugin = importlib.reload(importlib.import_module("plugin"))
        mod.clear_tool_decisions()
        original = {"command": "git status --short"}
        mod.on_tool_request(
            tool_name="terminal",
            args=dict(original),
            original_args=dict(original),
            tool_call_id="tool-hook-generic",
            session_id="session-hook",
            turn_id="turn-hook",
        )

        first = plugin.on_pre_tool_call(
            "terminal",
            original,
            task_id="task-hook",
            tool_call_id="tool-hook-generic",
            session_id="session-hook",
            turn_id="turn-hook",
        )
        second = plugin.on_pre_tool_call(
            "terminal",
            original,
            task_id="task-hook",
            tool_call_id="tool-hook-generic",
            session_id="session-hook",
            turn_id="turn-hook",
        )

        self.assertEqual("observe", first["action"])
        self.assertEqual("generic", first["feedback"]["kind"])
        self.assertIn("no specialized harness", first["feedback"]["text"])
        self.assertIsNone(second)

    def test_hmp_send_rewrite_runs_only_against_explicit_fake_server_override(self):
        received = []

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                length = int(self.headers.get("Content-Length", "0"))
                received.append((self.path, json.loads(self.rfile.read(length))))
                body = json.dumps({"accepted": True, "message_id": "fake-1", "status": "queued"}).encode()
                self.send_response(202)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *_args):
                return

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        os.environ["CAPABILITY_REUSE_TOOL_REUSE_MODE"] = "active"
        os.environ["CAPABILITY_REUSE_TEST_MODE"] = "1"
        os.environ["CAPABILITY_REUSE_ALLOW_SANDBOX_MUTATING"] = "1"
        os.environ["HMP_SEND_TARGET_OVERRIDE"] = f"http://127.0.0.1:{server.server_port}/hmp/send"
        os.environ["CAPABILITY_REUSE_PERMISSIONS"] = "hmp.network.read,hmp.network.write"
        os.environ["CAPABILITY_REUSE_ACTIVE_CAPABILITIES"] = "hmp-healthcheck,hmp-send"
        original_command = (
            "curl -sS -X POST http://192.168.178.141:18643/hmp/send "
            "-H 'Content-Type: application/json' -d '{\"to_peer\":\"peer141\",\"text\":\"hello sandbox\",\"session_id\":\"s1\"}'"
        )
        result = self._module().on_tool_request(
            tool_name="terminal",
            args={"command": original_command},
            original_args={"command": original_command},
            tool_call_id="tool-send-sandbox",
        )
        try:
            self.assertIsNotNone(result)
            self.assertNotIn(original_command, result["args"]["command"])
            completed = subprocess.run(
                result["args"]["command"],
                shell=True,
                capture_output=True,
                text=True,
                env=dict(os.environ),
                timeout=10,
            )
        finally:
            server.shutdown()
            thread.join(timeout=3)
            server.server_close()

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertEqual(1, len(received))
        self.assertEqual("/hmp/send", received[0][0])
        self.assertEqual("peer141", received[0][1]["to_peer"])
        self.assertEqual("hello sandbox", received[0][1]["text"])
        self.assertTrue(received[0][1]["idempotency_key"])

    def test_healthcheck_harness_cli_hits_fake_server_once(self):
        requests = []

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                requests.append(self.path)
                body = json.dumps({"status": "ok", "node_id": "fake"}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *_args):
                return

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        payload = Path(self._tmp.name) / "health-payload.json"
        payload.write_text(json.dumps({"peer_list": ["peer70"], "timeout_seconds": 2}))
        cli = ROOT / "plugin" / "harness_cli.py"
        env = dict(os.environ)
        env["CAPABILITY_REUSE_TEST_MODE"] = "1"
        env["HMP_HEALTH_TARGET_OVERRIDE"] = f"http://127.0.0.1:{server.server_port}/hmp/health"
        try:
            completed = subprocess.run(
                [sys.executable, str(cli), "hmp-healthcheck", "--payload-file", str(payload)],
                capture_output=True,
                text=True,
                env=env,
                timeout=10,
            )
        finally:
            server.shutdown()
            thread.join(timeout=3)
            server.server_close()

        self.assertEqual(0, completed.returncode, completed.stderr)
        result = json.loads(completed.stdout)
        self.assertTrue(result["success"])
        self.assertEqual(["/hmp/health"], requests)


if __name__ == "__main__":
    unittest.main()
