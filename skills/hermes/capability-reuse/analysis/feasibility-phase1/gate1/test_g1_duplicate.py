#!/usr/bin/env python3
"""Rebar Phase 1 — Gate 1 falsifier G4: DUPLICATE-SAFETY (idempotency semantics).

Question Gate 1 asks: *can the mechanism reject what it must reject?* G4's slice
is duplicate-safety / idempotency. A model-authored `curl .../messages/next`
declares a CONSUMING read: on the frozen G1 fake server GET /messages/next
returns AND CONSUMES the head message (the queue's `remaining` decrements), so
executing it more than once — a retry, or a substitute harness that runs its own
probe — drops/duplicates message consumption. The reviewed `hmp-healthcheck`
harness is an IDEMPOTENT probe (GET /health is read-only; running it any number
of times yields the same result and mutates nothing). Reusing the idempotent
harness for the non-idempotent consume would silently change at-most-once
semantics.

Per the frozen plan (§Task G4) the mechanism MUST, for a caller whose requested
operation is a NON-IDEMPOTENT consume, decline substitution with
`reason=idempotency_mismatch` and perform NO substitution. Crucially: **a decline
for an UNRELATED reason (e.g. unknown endpoint / unsupported target) must NOT
count** as the mechanism enforcing duplicate-safety — the *idempotency* (a
consuming op vs an idempotent GET /health, same host, same method class) must be
the demonstrated cause.

This is NOT a unit test of compatibility logic. It drives the REAL Hermes tool
middleware (`apply_tool_request_middleware` — the exact function
`agent/tool_executor.py` calls), against the FROZEN G1 fake HMP server
(gate1/fake_hmp_server.py, reviewed baseline sha adb729…), mirroring
`scripts/t5-real-middleware-proof.py` and the accepted G2/G3 falsifiers
(test_g1_timeout.py / test_g1_effect.py).

Run:  python3 test_g1_duplicate.py   (prints JSON verdict; exit 0 iff enforcement present)

Outcome semantics:
  * verdict FALSIFIER_FIRED  -> the duplicate-safety enforcement point is ABSENT
                                (mechanism substitutes an idempotent harness for a
                                non-idempotent consume, or declines for an
                                unrelated reason)
  * verdict ENFORCED         -> mechanism declines with idempotency_mismatch, and
                                the IDEMPOTENCY is the proven discriminator (an
                                idempotent GET /health substitutes while the
                                consuming GET /messages/next is declined).

A FIRED verdict is a Gate-1 NARROW/REWORK finding, not a harness bug.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import urllib.request
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


def _known_peer() -> tuple[str, str]:
    """Return (peer, base_curl_prefix) whose host is a real PEER_MAP peer, so the
    ONLY thing that can stop substitution is genuine duplicate-safety enforcement
    (a consuming op), not an unsupported-target decline."""
    sys.path.insert(0, str(PLUGIN_DIR))
    from execution_plan import PEER_MAP  # noqa: E402
    peer, (ip, _path) = next(iter(PEER_MAP.items()))
    return peer, f"http://{ip}:18643"


def _get(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=10) as r:
        return json.loads(r.read().decode("utf-8"))


def _post(url: str, body: dict) -> dict:
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST",
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read().decode("utf-8"))


def _decision_reason(plugin_mod, tool_call_id: str) -> tuple[bool, str]:
    """Return (will_rewrite, reason) for a consumed tool decision."""
    consumed = plugin_mod.consume_tool_decision(tool_call_id)
    dec_obj = consumed.get("decision") if isinstance(consumed, dict) else None
    reason = getattr(dec_obj, "reason", "") if dec_obj is not None else ""
    will_rewrite = bool(getattr(dec_obj, "will_rewrite", False)) if dec_obj is not None else False
    return will_rewrite, reason


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
    from hermes_cli.middleware import apply_tool_request_middleware

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
    if plugin_mod is None:
        return finish()

    # -- FROZEN G1 fake server: establish the GROUND-TRUTH idempotency asymmetry
    # This is not nominal: on the reviewed fake server GET /health is IDEMPOTENT
    # (repeat calls return identical mutations=0) while GET /messages/next is
    # NON-IDEMPOTENT (each call CONSUMES the head message and decrements
    # `remaining`). Proving the two genuinely differ in idempotency is what makes
    # an idempotency_mismatch decline meaningful rather than a label game.
    srv, thread, base = fake.serve_in_thread(0, slow_delay=0.05)
    peer, curl_prefix = _known_peer()
    try:
        # ---- ground truth: GET /health is idempotent -----------------------
        h1 = _get(f"{base}/health")
        h2 = _get(f"{base}/health")
        health_idempotent = h1["mutations"] == h2["mutations"] == 0 and h1 == h2
        check("ground_truth_health_is_idempotent", health_idempotent,
              {"health_1": h1.get("mutations"), "health_2": h2.get("mutations")})

        # ---- ground truth: GET /messages/next CONSUMES (non-idempotent) -----
        _post(f"{base}/admin/state", {"enqueue": ["m-alpha", "m-beta"]})
        c1 = _get(f"{base}/messages/next")
        c2 = _get(f"{base}/messages/next")
        c3 = _get(f"{base}/messages/next")
        consume_non_idempotent = (
            c1.get("message") == "m-alpha" and c1.get("remaining") == 1
            and c2.get("message") == "m-beta" and c2.get("remaining") == 0
            and c3.get("message") is None
        )
        check("ground_truth_consume_is_non_idempotent", consume_non_idempotent,
              {"consume_1": c1.get("message"), "remaining_1": c1.get("remaining"),
               "consume_2": c2.get("message"), "remaining_2": c2.get("remaining"),
               "consume_3": c3.get("message")})

        # ---- CANONICAL: consuming GET /messages/next to a RECOGNIZED peer ---
        # Same host + read-method (GET) as the substitutable /health below; only
        # the IDEMPOTENCY (consuming vs idempotent) differs. The mechanism must
        # decline with a duplicate-safety-specific reason and perform NO
        # substitution.
        consume_command = f"curl -sS {curl_prefix}/messages/next"
        plugin_mod.clear_tool_decisions()
        consume_result = apply_tool_request_middleware(
            "terminal", {"command": consume_command}, skip_relay=True,
            task_id="g4", session_id="g4", tool_call_id="g4-canonical-consume",
            turn_id="g4", api_request_id="g4",
        )
        consume_substituted = bool(getattr(consume_result, "changed", False)) and \
            getattr(consume_result, "payload", {}).get("command") != consume_command
        consume_rewrite, consume_reason = _decision_reason(plugin_mod, "g4-canonical-consume")
        dup_enforced = (not consume_substituted) and (not consume_rewrite) and \
            consume_reason == "idempotency_mismatch"
        check("duplicate_safety_enforcement_point_present", dup_enforced,
              {"substituted": consume_substituted, "reason": consume_reason,
               "expected_reason": "idempotency_mismatch"})

        # ---- IDEMPOTENCY IS THE CAUSE: an idempotent GET /health substitutes -
        # Isolates the discriminator: with the same host and the same HTTP method
        # class (GET), an IDEMPOTENT /health is reused, so the consume decline
        # above was caused by IDEMPOTENCY, not by target/host/method.
        health_command = f"curl -sS {curl_prefix}/health"
        health_result = apply_tool_request_middleware(
            "terminal", {"command": health_command}, skip_relay=True,
            task_id="g4", session_id="g4", tool_call_id="g4-control-health",
            turn_id="g4", api_request_id="g4",
        )
        health_substituted = bool(getattr(health_result, "changed", False)) and \
            getattr(health_result, "payload", {}).get("command") != health_command
        health_rewrite, health_reason = _decision_reason(plugin_mod, "g4-control-health")
        idempotency_is_cause = (health_substituted or health_rewrite) and dup_enforced
        check("idempotency_is_the_discriminator", idempotency_is_cause,
              {"health_substituted": health_substituted, "health_rewrite": health_rewrite,
               "health_reason": health_reason,
               "note": "same host/method-class: idempotent /health reused, "
                       "consuming /messages/next declined => idempotency is the cause"})

        # ---- CONTROL: unrelated-reason decline must NOT be credited ---------
        # A GET to an UNKNOWN endpoint also declines, but for a DIFFERENT reason
        # (unrecognized_endpoint), proving "any decline == duplicate-safety
        # enforcement" is false.
        unrelated_command = f"curl -sS {curl_prefix}/not-a-known-endpoint"
        apply_tool_request_middleware(
            "terminal", {"command": unrelated_command}, skip_relay=True,
            task_id="g4", session_id="g4", tool_call_id="g4-control-unrelated",
            turn_id="g4", api_request_id="g4",
        )
        _, unrelated_reason = _decision_reason(plugin_mod, "g4-control-unrelated")
        check("control_decline_is_unrelated_reason",
              bool(unrelated_reason) and unrelated_reason != "idempotency_mismatch",
              {"control_reason": unrelated_reason})

        # ---- duplicate-safety enforcement lives ON THE ENFORCEMENT PATH -----
        # The decline must originate in tool_reuse.py (derive/decide_operation),
        # the exact functions the real tool middleware calls — not in an
        # off-path scorer.
        enforce_src = (PLUGIN_DIR / "tool_reuse.py").read_text(
            encoding="utf-8", errors="replace")
        check("duplicate_safety_on_enforcement_path", "idempotency_mismatch" in enforce_src,
              {"tool_reuse_has_idempotency_mismatch": "idempotency_mismatch" in enforce_src})
    finally:
        srv.shutdown()
        srv.server_close()

    return finish()


def finish() -> int:
    enforced = (
        RESULTS.get("duplicate_safety_enforcement_point_present", False)
        and RESULTS.get("idempotency_is_the_discriminator", False)
        and RESULTS.get("duplicate_safety_on_enforcement_path", False)
        and RESULTS.get("control_decline_is_unrelated_reason", False)
    )
    verdict = "ENFORCED" if enforced else "FALSIFIER_FIRED"
    print(json.dumps({
        "gate": "G4_duplicate_safety",
        "verdict": verdict,
        "checks": RESULTS,
        "details": DETAILS,
        "finding": (
            "OK — mechanism declines reuse for a non-idempotent consume with "
            "reason=idempotency_mismatch; idempotency (consuming /messages/next "
            "vs idempotent /health on the same host/method-class) is the proven "
            "discriminator."
            if enforced else
            "DEFECT — no duplicate-safety enforcement point: the mechanism would "
            "reuse the idempotent hmp-healthcheck harness for a non-idempotent "
            "consume (silently changing at-most-once semantics / risking a "
            "duplicate consume), or declined for an unrelated reason. Gate-1 "
            "NARROW/REWORK candidate."
        ),
    }, indent=2, sort_keys=True))
    return 0 if enforced else 1


def main() -> int:
    tmp_home = Path(tempfile.mkdtemp(prefix="rebar-g4-home-"))
    try:
        return run(tmp_home)
    finally:
        shutil.rmtree(tmp_home, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
