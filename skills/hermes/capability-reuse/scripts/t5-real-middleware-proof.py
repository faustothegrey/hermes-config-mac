#!/usr/bin/env python3
"""T5 driver — real Hermes middleware integration proof (charter §8.10).

Runs INSIDE an isolated HERMES_HOME so the real PluginManager discovers the
capability-reuse plugin from staged source bytes, registers its
``tool_request`` middleware through the real ``register_middleware`` API,
and the real ``apply_tool_request_middleware`` / ``run_tool_execution_middleware``
chain (the exact functions ``agent/tool_executor.py`` calls) rewrites a
model-authored HMP healthcheck curl into the reviewed harness CLI.

Checks (agreed plan Phase B / T5 gate):
  1. real discovery loads the plugin and registers tool_request middleware;
  2. rewrite changes ONLY ``command``; other args preserved;
  3. middleware trace carries {source: capability-reuse, reason, name};
  4. original model-authored curl bytes never execute;
  5. fake server receives exactly one request, from the harness;
  6. exactly one truthful decision record per tool_call_id (single-fire);
  7. concurrent calls each decided exactly once, no cross-talk;
  8. middleware failure is fail-open (original args untouched);
  9. shadow mode never rewrites (Phase A invariant).

Prints a JSON verdict on stdout; exit 0 only if every check passes.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERMES_AGENT = Path.home() / ".hermes" / "hermes-agent"
SOURCE_PLUGIN = Path(__file__).resolve().parents[1] / "plugin"

RESULTS: dict[str, bool] = {}
DETAILS: dict[str, str] = {}


def check(name: str, ok: bool, detail: str = "") -> None:
    RESULTS[name] = bool(ok)
    if detail:
        DETAILS[name] = detail


def main() -> int:
    tmp_home = Path(tempfile.mkdtemp(prefix="rebar-t5-home-"))
    try:
        return run(tmp_home)
    finally:
        shutil.rmtree(tmp_home, ignore_errors=True)


def run(tmp_home: Path) -> int:
    # -- stage isolated HERMES_HOME with the SOURCE plugin bytes ----------
    staged = tmp_home / "plugins" / "capability-reuse"
    shutil.copytree(SOURCE_PLUGIN, staged, ignore=shutil.ignore_patterns("__pycache__", "r2-*"))
    (tmp_home / "config.yaml").write_text(
        "plugins:\n  enabled:\n    - capability-reuse\n  disabled: []\n"
    )
    harness_input_dir = tmp_home / "harness-inputs"
    os.environ["HERMES_HOME"] = str(tmp_home)
    os.environ["CAPABILITY_REUSE_HARNESS_INPUT_DIR"] = str(harness_input_dir)
    os.environ["CAPABILITY_REUSE_PERMISSIONS"] = "hmp.network.read"
    os.environ["CAPABILITY_REUSE_AVAILABLE_CAPABILITIES"] = "hmp_client_installed"
    os.environ["CAPABILITY_REUSE_ACTIVE_CAPABILITIES"] = "hmp-healthcheck"
    os.environ["CAPABILITY_REUSE_TOOL_REUSE_MODE"] = "active"
    os.environ["CAPABILITY_REUSE_TEST_MODE"] = "1"

    sys.path.insert(0, str(HERMES_AGENT))
    import hermes_cli.plugins as plugins_mod
    from hermes_cli.middleware import (
        apply_tool_request_middleware,
        run_tool_execution_middleware,
    )

    # -- 1. real discovery + middleware registration ----------------------
    manager = plugins_mod.get_plugin_manager()
    has_mw = plugins_mod.has_middleware("tool_request")
    loaded = [p for p in getattr(manager, "_plugins", {}) or []]
    check("discovery_registers_middleware", has_mw,
          f"plugins={loaded!r} has_tool_request={has_mw}")
    if not has_mw:
        return finish()

    plugin_mod = sys.modules.get("tool_reuse")
    for name, mod in list(sys.modules.items()):
        if name.endswith("tool_reuse") and hasattr(mod, "consume_tool_decision"):
            plugin_mod = mod
            break
    check("tool_reuse_module_importable", plugin_mod is not None)

    # -- fake HMP health server -------------------------------------------
    hits: list[str] = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            hits.append(self.path)
            body = json.dumps({"status": "ok", "node_id": "fake-peer70"}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *_a):
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    os.environ["HMP_HEALTH_TARGET_OVERRIDE"] = (
        f"http://127.0.0.1:{server.server_port}/hmp/health"
    )

    original_command = "curl -sS --max-time 5 http://192.168.178.70:18643/hmp/health"
    original_args = {
        "command": original_command,
        "workdir": "/tmp",
        "timeout": 60,
        "background": False,
    }

    try:
        # -- 2/3. real apply_tool_request_middleware ----------------------
        result = apply_tool_request_middleware(
            "terminal",
            dict(original_args),
            skip_relay=True,
            task_id="t5-task",
            session_id="t5-session",
            tool_call_id="t5-call-1",
            turn_id="t5-turn",
            api_request_id="t5-api",
        )
        rewritten = result.payload
        check("rewrite_happened", result.changed and
              rewritten["command"] != original_command)
        check("only_command_rewritten", all(
            rewritten.get(k) == original_args[k]
            for k in ("workdir", "timeout", "background")
        ), f"rewritten={rewritten!r}")
        trace_entry = next(
            (t for t in result.trace if t.get("source") == "capability-reuse"), None
        )
        check("trace_carries_identity",
              bool(trace_entry)
              and trace_entry.get("name") == "hmp-healthcheck@1.0.0"
              and trace_entry.get("reason") == "harness_reuse",
              f"trace={result.trace!r}")
        check("original_bytes_absent",
              original_command not in rewritten["command"],
              rewritten["command"])

        # -- 4/5. real run_tool_execution_middleware → dispatch -----------
        executed_commands: list[str] = []

        def dispatch(args_for_exec):
            cmd = args_for_exec["command"]
            executed_commands.append(cmd)
            return subprocess.run(
                cmd, shell=True, capture_output=True, text=True,
                env=dict(os.environ), timeout=20,
            )

        completed = run_tool_execution_middleware(
            "terminal",
            rewritten,
            dispatch,
            original_args=dict(original_args),
            task_id="t5-task",
            session_id="t5-session",
            tool_call_id="t5-call-1",
            turn_id="t5-turn",
            api_request_id="t5-api",
        )
        check("dispatch_executed_once", len(executed_commands) == 1)
        check("dispatched_bytes_are_harness",
              original_command not in executed_commands[0]
              and "harness_cli.py" in executed_commands[0],
              executed_commands[0])
        ok_exec = completed.returncode == 0
        payload_out = {}
        if ok_exec:
            try:
                payload_out = json.loads(completed.stdout)
            except json.JSONDecodeError:
                ok_exec = False
        check("harness_result_success",
              ok_exec and payload_out.get("success") is True,
              completed.stderr[-400:] if completed.stderr else completed.stdout[-400:])
        check("fake_server_exactly_one_hit", hits == ["/hmp/health"], repr(hits))

        # -- 6. exactly-once truthful decision ----------------------------
        first = plugin_mod.consume_tool_decision("t5-call-1")
        second = plugin_mod.consume_tool_decision("t5-call-1")
        check("decision_single_fire",
              first is not None and second is None
              and first.get("kind") == "matched"
              and "hmp-healthcheck@1.0.0 reused" in first.get("text", ""),
              repr(first))

        # -- 7. concurrent exactly-once -----------------------------------
        errors: list[str] = []

        def worker(call_id: str, command: str):
            try:
                apply_tool_request_middleware(
                    "terminal", {"command": command},
                    skip_relay=True, tool_call_id=call_id,
                    session_id="t5-session", task_id="t5-task",
                    turn_id="t5-turn", api_request_id="t5-api",
                )
            except Exception as exc:  # pragma: no cover
                errors.append(f"{call_id}: {exc}")

        threads = [
            threading.Thread(target=worker, args=("t5-conc-a", "git status --short")),
            threading.Thread(target=worker, args=("t5-conc-b", "echo hello")),
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)
        conc_a = plugin_mod.consume_tool_decision("t5-conc-a")
        conc_b = plugin_mod.consume_tool_decision("t5-conc-b")
        check("concurrent_each_decided_once",
              not errors
              and conc_a is not None and conc_b is not None
              and plugin_mod.consume_tool_decision("t5-conc-a") is None
              and plugin_mod.consume_tool_decision("t5-conc-b") is None
              and conc_a.get("kind") == "generic"
              and conc_b.get("kind") == "generic",
              f"errors={errors!r} a={conc_a!r} b={conc_b!r}")

        # -- 8. fail-open on middleware exception --------------------------
        real_derive = plugin_mod.derive_operation

        def boom(*_a, **_k):
            raise RuntimeError("t5 injected failure")

        plugin_mod.derive_operation = boom
        try:
            failed = apply_tool_request_middleware(
                "terminal", dict(original_args),
                skip_relay=True, tool_call_id="t5-fail",
                session_id="t5-session", task_id="t5-task",
                turn_id="t5-turn", api_request_id="t5-api",
            )
            check("failure_is_fail_open",
                  failed.payload["command"] == original_command
                  and not any(
                      t.get("source") == "capability-reuse" for t in failed.trace),
                  repr(failed.trace))
        finally:
            plugin_mod.derive_operation = real_derive

        # -- 9. shadow mode never rewrites (Phase A invariant) -------------
        os.environ["CAPABILITY_REUSE_TOOL_REUSE_MODE"] = "shadow"
        shadow = apply_tool_request_middleware(
            "terminal", dict(original_args),
            skip_relay=True, tool_call_id="t5-shadow",
            session_id="t5-session", task_id="t5-task",
            turn_id="t5-turn", api_request_id="t5-api",
        )
        shadow_decision = plugin_mod.consume_tool_decision("t5-shadow")
        check("shadow_mode_no_rewrite",
              shadow.payload["command"] == original_command
              and shadow_decision is not None
              and shadow_decision.get("kind") == "rejected"
              and "shadow_mode" in shadow_decision.get("text", ""),
              repr(shadow_decision))
    finally:
        server.shutdown()
        server.server_close()

    return finish()


def finish() -> int:
    verdict = all(RESULTS.values()) and len(RESULTS) >= 12
    print(json.dumps({
        "verdict": "PASS" if verdict else "FAIL",
        "checks": RESULTS,
        "details": DETAILS,
        "total": len(RESULTS),
        "passed": sum(1 for v in RESULTS.values() if v),
    }, indent=2))
    return 0 if verdict else 1


if __name__ == "__main__":
    sys.exit(main())
