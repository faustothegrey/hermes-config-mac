#!/usr/bin/env python3
"""Rebar Phase 1 — Gate 1 falsifier G2: TIMEOUT SEMANTICS.

Question Gate 1 asks: *can the mechanism reject what it must reject?* G2's slice
is timeout semantics. A model-authored `curl --max-time T` declares a
WHOLE-REQUEST time budget (connect + transfer, one hard deadline). The reviewed
`hmp-healthcheck` harness honours timeouts via `urllib.request.urlopen(timeout=)`,
which is a PER-OPERATION socket timeout — a DIFFERENT semantic class. Substituting
the harness for the curl therefore changes what "timeout" means.

Per the frozen plan (§Task G2) the mechanism MUST, for a caller whose whole-request
budget cannot be faithfully honoured by the reused harness, emit
`whole_request_covered=false`, `reason=timeout_semantics_mismatch`, and perform NO
substitution. Crucially: **a decline for an UNRELATED reason (e.g. unknown endpoint)
must NOT count** as the mechanism enforcing timeout semantics.

This is NOT a unit test of compatibility logic. It drives the REAL Hermes tool
middleware (`apply_tool_request_middleware` / `run_tool_execution_middleware` — the
exact functions `agent/tool_executor.py` calls), against the FROZEN G1 fake HMP
server (gate1/fake_hmp_server.py, reviewed baseline), mirroring
`scripts/t5-real-middleware-proof.py`.

Run:  python3 test_g1_timeout.py    (prints JSON verdict; exit 0 iff enforcement present)

Outcome semantics:
  * verdict FALSIFIER_FIRED  -> the timeout-semantics enforcement point is ABSENT
                                (mechanism substitutes anyway / mangles the budget)
  * verdict ENFORCED         -> mechanism declines with timeout_semantics_mismatch.

A FIRED verdict is a Gate-1 NARROW/REWORK finding, not a harness bug.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import threading
from pathlib import Path

GATE1_DIR = Path(__file__).resolve().parent
PLUGIN_DIR = GATE1_DIR.parents[2] / "plugin"          # .../capability-reuse/plugin
HERMES_AGENT = Path.home() / ".hermes" / "hermes-agent"

# frozen G1 server (reviewed baseline — do NOT reimplement the target here)
sys.path.insert(0, str(GATE1_DIR))
import fake_hmp_server as fake  # noqa: E402

RESULTS: dict[str, bool] = {}
DETAILS: dict[str, object] = {}


def check(name: str, ok: bool, detail: object = "") -> None:
    RESULTS[name] = bool(ok)
    if detail != "":
        DETAILS[name] = detail


def _known_peer_health_url() -> str:
    """A curl URL whose host is a real PEER_MAP peer and whose path is a
    RECOGNIZED health endpoint, so the ONLY thing that can stop substitution is
    genuine timeout-semantics enforcement (not an unknown-endpoint decline)."""
    sys.path.insert(0, str(PLUGIN_DIR))
    from execution_plan import PEER_MAP  # noqa: E402
    peer, (ip, path) = next(iter(PEER_MAP.items()))
    return peer, f"http://{ip}:18643{path.rstrip('/') or '/health'}"


def run(tmp_home: Path) -> int:
    # -- stage isolated HERMES_HOME with SOURCE plugin bytes (t5 pattern) ----
    staged = tmp_home / "plugins" / "capability-reuse"
    shutil.copytree(PLUGIN_DIR, staged, ignore=shutil.ignore_patterns("__pycache__", "r2-*"))
    (tmp_home / "config.yaml").write_text(
        "plugins:\n  enabled:\n    - capability-reuse\n  disabled: []\n"
    )
    os.environ["HERMES_HOME"] = str(tmp_home)
    os.environ["CAPABILITY_REUSE_HARNESS_INPUT_DIR"] = str(tmp_home / "harness-inputs")
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

    manager = plugins_mod.get_plugin_manager()
    has_mw = plugins_mod.has_middleware("tool_request")
    check("real_middleware_registered", has_mw,
          f"plugins={list(getattr(manager, '_plugins', {}) or [])!r}")
    if not has_mw:
        return finish()

    plugin_mod = None
    for name, mod in list(sys.modules.items()):
        if name.endswith("tool_reuse") and hasattr(mod, "consume_tool_decision"):
            plugin_mod = mod
            break
    check("tool_reuse_importable", plugin_mod is not None)

    # -- FROZEN G1 fake server with a genuinely slow health endpoint --------
    srv, thread, base = fake.serve_in_thread(0, slow_delay=2.0)
    peer, recognized_curl_url = _known_peer_health_url()
    try:
        # The harness's ACTUAL probe is redirected to the frozen G1 /slow-health
        # (2s). The caller's declared whole-request budget is 0.2s.
        os.environ["HMP_HEALTH_TARGET_OVERRIDE"] = f"{base}/slow-health"

        BUDGET = "0.2"  # sub-second whole-request deadline
        original_command = (
            f"curl -sS --max-time {BUDGET} {recognized_curl_url}"
        )
        original_args = {"command": original_command, "workdir": "/tmp",
                         "timeout": 60, "background": False}

        result = apply_tool_request_middleware(
            "terminal", dict(original_args), skip_relay=True,
            task_id="g2", session_id="g2", tool_call_id="g2-canonical",
            turn_id="g2", api_request_id="g2",
        )
        decision = plugin_mod.consume_tool_decision("g2-canonical")
        substituted = bool(result.changed) and result.payload["command"] != original_command

        # ---- ENFORCEMENT POINT (what the plan REQUIRES) -------------------
        # The mechanism must decline substitution with a TIMEOUT-SPECIFIC reason.
        reason = ""
        dec_obj = decision.get("decision") if isinstance(decision, dict) else None
        if dec_obj is not None:
            reason = getattr(dec_obj, "reason", "")
        enforced = (not substituted) and reason == "timeout_semantics_mismatch"
        check("enforcement_point_present", enforced,
              {"substituted": substituted, "reason": reason,
               "expected_reason": "timeout_semantics_mismatch"})

        # ---- timeout-semantics coverage must exist ON THE ENFORCEMENT PATH -
        # NB: the plugin DOES carry a `whole_request_covered` signal, but only
        # in retriever.py's candidate-SCORING path, where `_coverage_reason`
        # encodes EFFECT coverage (read_only vs mutating) with NO timeout notion,
        # and it is NOT consulted by the tool-boundary decision
        # (tool_reuse.decide_operation). The enforcement path is what actually
        # gates substitution, so THAT is where a timeout-semantics concept must
        # live for G2 to be enforced.
        enforce_src = (PLUGIN_DIR / "tool_reuse.py").read_text(
            encoding="utf-8", errors="replace").lower()
        enforce_has_timeout_semantics = any(
            tok in enforce_src for tok in
            ("timeout_semantics", "whole_request_covered", "request_deadline"))
        retr_src = (PLUGIN_DIR / "retriever.py").read_text(
            encoding="utf-8", errors="replace").lower()
        retr_has_whole_request = "whole_request_covered" in retr_src
        check("timeout_semantics_on_enforcement_path", enforce_has_timeout_semantics,
              {"tool_reuse_has_timeout_semantics": enforce_has_timeout_semantics,
               "retriever_has_whole_request_covered_effect_only": retr_has_whole_request,
               "note": "retriever whole_request_covered encodes effect coverage, "
                       "not timeout, and is off the enforcement path"})

        # ---- fractional budget must be preserved, not truncated to 0 ------
        # int(float("0.2")) == 0: the harness would probe with socket timeout 0.
        derived_timeout = None
        if dec_obj is not None:
            derived_timeout = getattr(dec_obj, "inputs", {}).get("timeout_seconds")
        budget_preserved = derived_timeout is not None and float(derived_timeout) >= float(BUDGET)
        check("subsecond_budget_preserved", budget_preserved,
              {"declared_budget_s": float(BUDGET), "harness_timeout_seconds": derived_timeout})

        # ---- CONTROL: unrelated-reason decline must NOT be credited -------
        # /slow-health is an UNKNOWN endpoint to the mechanism -> it declines,
        # but for reason 'unrecognized_endpoint', NOT timeout semantics.
        unrelated_cmd = f"curl -sS --max-time {BUDGET} {base}/slow-health"
        apply_tool_request_middleware(
            "terminal", {"command": unrelated_cmd}, skip_relay=True,
            task_id="g2", session_id="g2", tool_call_id="g2-control",
            turn_id="g2", api_request_id="g2",
        )
        ctrl = plugin_mod.consume_tool_decision("g2-control")
        ctrl_obj = ctrl.get("decision") if isinstance(ctrl, dict) else None
        ctrl_reason = getattr(ctrl_obj, "reason", "") if ctrl_obj else ""
        # This control passes when the decline reason is demonstrably UNRELATED
        # to timeout semantics (proving "any decline == enforcement" is false).
        check("control_decline_is_unrelated_reason",
              ctrl_reason and ctrl_reason != "timeout_semantics_mismatch",
              {"control_reason": ctrl_reason})

        # ---- semantic class: harness uses per-op socket timeout -----------
        harness_src = (PLUGIN_DIR / "harness_cli.py").read_text(encoding="utf-8")
        per_op = "urlopen(request, timeout=timeout_seconds)" in harness_src
        check("harness_uses_per_op_socket_timeout", per_op,
              {"note": "urllib urlopen(timeout=) is per-operation, not a whole-request deadline"})
    finally:
        srv.shutdown()
        srv.server_close()

    return finish()


def finish() -> int:
    # The falsifier FIRES (defect found) unless the enforcement point is present
    # AND the budget is faithfully preserved.
    enforced = RESULTS.get("enforcement_point_present", False) and \
        RESULTS.get("subsecond_budget_preserved", False) and \
        RESULTS.get("timeout_semantics_on_enforcement_path", False)
    verdict = "ENFORCED" if enforced else "FALSIFIER_FIRED"
    print(json.dumps({
        "gate": "G2_timeout_semantics",
        "verdict": verdict,
        "checks": RESULTS,
        "details": DETAILS,
        "finding": (
            "OK — mechanism declines timeout-semantics mismatch."
            if enforced else
            "DEFECT — no timeout-semantics enforcement point: the mechanism "
            "substitutes the reviewed harness for a whole-request --max-time "
            "curl, silently coerces the whole-request budget into a per-op "
            "socket timeout, and truncates sub-second budgets to 0 "
            "(int(float('0.2'))==0). Gate-1 NARROW/REWORK candidate."
        ),
    }, indent=2, sort_keys=True))
    return 0 if enforced else 1


def main() -> int:
    tmp_home = Path(tempfile.mkdtemp(prefix="rebar-g2-home-"))
    try:
        return run(tmp_home)
    finally:
        shutil.rmtree(tmp_home, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
