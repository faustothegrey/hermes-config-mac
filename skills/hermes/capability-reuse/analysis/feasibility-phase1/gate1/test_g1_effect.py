#!/usr/bin/env python3
"""Rebar Phase 1 — Gate 1 falsifier G3: EFFECT SEMANTICS.

Question Gate 1 asks: *can the mechanism reject what it must reject?* G3's slice
is effect semantics. A model-authored `curl -X POST .../health` declares a
MUTATING operation (POST /health, on the frozen G1 fake server, increments an
observable counter — a genuine state change). The reviewed `hmp-healthcheck`
harness is a READ-ONLY health probe (GET). Substituting the read-only harness
for a mutating POST would silently change what the operation DOES.

Per the frozen plan (§Task G3) the mechanism MUST, for a caller whose requested
operation is a mutating POST against a health endpoint the harness only covers
read-only, decline substitution with `reason=effect_mismatch` and perform NO
substitution. Crucially: **a decline for an UNRELATED reason (e.g. unknown
endpoint / unsupported target) must NOT count** as the mechanism enforcing
effect semantics — the *effect* (POST vs GET) must be the demonstrated cause.

This is NOT a unit test of compatibility logic. It drives the REAL Hermes tool
middleware (`apply_tool_request_middleware` — the exact function
`agent/tool_executor.py` calls), against the FROZEN G1 fake HMP server
(gate1/fake_hmp_server.py, reviewed baseline sha adb729…), mirroring
`scripts/t5-real-middleware-proof.py` and the accepted G2 falsifier
(test_g1_timeout.py).

Run:  python3 test_g1_effect.py    (prints JSON verdict; exit 0 iff enforcement present)

Outcome semantics:
  * verdict FALSIFIER_FIRED  -> the effect-semantics enforcement point is ABSENT
                                (mechanism substitutes a read-only harness for a
                                mutating POST, or declines for an unrelated reason)
  * verdict ENFORCED         -> mechanism declines with effect_mismatch, and the
                                EFFECT is the proven discriminator (same URL, GET
                                substitutes while POST is declined).

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


def _known_peer_health_url() -> tuple[str, str]:
    """A curl URL whose host is a real PEER_MAP peer and whose path is a
    RECOGNIZED health endpoint, so the ONLY thing that can stop substitution is
    genuine effect-semantics enforcement (POST vs GET), not an unknown-endpoint
    or unsupported-target decline."""
    sys.path.insert(0, str(PLUGIN_DIR))
    from execution_plan import PEER_MAP  # noqa: E402
    peer, (ip, path) = next(iter(PEER_MAP.items()))
    return peer, f"http://{ip}:18643{path.rstrip('/') or '/health'}"


def _post(url: str) -> dict:
    req = urllib.request.Request(url, data=b"{}", method="POST",
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read().decode("utf-8"))


def _get(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=10) as r:
        return json.loads(r.read().decode("utf-8"))


def _decision_reason(plugin_mod, tool_call_id: str) -> tuple[bool, str]:
    """Return (substituted, reason) for a consumed tool decision."""
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

    # -- FROZEN G1 fake server: establish the GROUND-TRUTH effect asymmetry --
    # This is not nominal: on the reviewed fake server GET /health is read-only
    # (mutations stays 0) while POST /health MUTATES (increments the counter).
    # Proving the two methods genuinely differ in EFFECT is what makes an
    # effect_mismatch decline meaningful rather than a label game.
    srv, thread, base = fake.serve_in_thread(0, slow_delay=0.05)
    peer, recognized_curl_url = _known_peer_health_url()
    try:
        before = _get(f"{base}/health")
        _get(f"{base}/health")
        mid = _get(f"{base}/health")
        get_is_read_only = mid["mutations"] == before["mutations"] == 0
        check("ground_truth_get_is_read_only", get_is_read_only,
              {"mutations_after_gets": mid["mutations"]})

        posted = _post(f"{base}/health")
        after = _get(f"{base}/health")
        post_mutates = posted["effect"] == "mutated" and after["mutations"] >= 1
        check("ground_truth_post_mutates", post_mutates,
              {"post_effect": posted.get("effect"), "mutations_after_post": after["mutations"]})

        # ---- CANONICAL: mutating POST to a RECOGNIZED health endpoint --------
        # Same host + same recognized path as the substitutable GET below; only
        # the METHOD (effect) differs. The mechanism must decline with an
        # effect-specific reason and perform NO substitution.
        post_command = f"curl -sS -X POST {recognized_curl_url}"
        plugin_mod.clear_tool_decisions()
        post_result = apply_tool_request_middleware(
            "terminal", {"command": post_command}, skip_relay=True,
            task_id="g3", session_id="g3", tool_call_id="g3-canonical-post",
            turn_id="g3", api_request_id="g3",
        )
        post_substituted = bool(getattr(post_result, "changed", False)) and \
            getattr(post_result, "payload", {}).get("command") != post_command
        post_rewrite, post_reason = _decision_reason(plugin_mod, "g3-canonical-post")
        effect_enforced = (not post_substituted) and (not post_rewrite) and \
            post_reason == "effect_mismatch"
        check("effect_enforcement_point_present", effect_enforced,
              {"substituted": post_substituted, "reason": post_reason,
               "expected_reason": "effect_mismatch"})

        # ---- EFFECT IS THE CAUSE: same URL as GET DOES substitute -----------
        # Isolates the discriminator: with everything else identical, a GET
        # (read-only) to the SAME recognized endpoint is reused, so the POST
        # decline above was caused by the EFFECT, not by target/endpoint.
        get_command = f"curl -sS {recognized_curl_url}"
        get_result = apply_tool_request_middleware(
            "terminal", {"command": get_command}, skip_relay=True,
            task_id="g3", session_id="g3", tool_call_id="g3-control-get",
            turn_id="g3", api_request_id="g3",
        )
        get_substituted = bool(getattr(get_result, "changed", False)) and \
            getattr(get_result, "payload", {}).get("command") != get_command
        get_rewrite, get_reason = _decision_reason(plugin_mod, "g3-control-get")
        effect_is_cause = (get_substituted or get_rewrite) and effect_enforced
        check("effect_is_the_discriminator", effect_is_cause,
              {"get_substituted": get_substituted, "get_rewrite": get_rewrite,
               "get_reason": get_reason,
               "note": "same recognized URL: GET reused, POST declined => effect is the cause"})

        # ---- CONTROL: unrelated-reason decline must NOT be credited ---------
        # A POST to an UNKNOWN endpoint also declines, but for a DIFFERENT
        # reason (unrecognized_endpoint), proving "any decline == effect
        # enforcement" is false.
        unrelated_command = f"curl -sS -X POST {recognized_curl_url.rsplit('/', 1)[0]}/not-a-health-endpoint"
        apply_tool_request_middleware(
            "terminal", {"command": unrelated_command}, skip_relay=True,
            task_id="g3", session_id="g3", tool_call_id="g3-control-unrelated",
            turn_id="g3", api_request_id="g3",
        )
        _, unrelated_reason = _decision_reason(plugin_mod, "g3-control-unrelated")
        check("control_decline_is_unrelated_reason",
              bool(unrelated_reason) and unrelated_reason != "effect_mismatch",
              {"control_reason": unrelated_reason})

        # ---- effect-semantics enforcement lives ON THE ENFORCEMENT PATH -----
        # The decline must originate in tool_reuse.py (derive/decide_operation),
        # the exact functions the real tool middleware calls — not in an
        # off-path scorer.
        enforce_src = (PLUGIN_DIR / "tool_reuse.py").read_text(
            encoding="utf-8", errors="replace")
        check("effect_semantics_on_enforcement_path", "effect_mismatch" in enforce_src,
              {"tool_reuse_has_effect_mismatch": "effect_mismatch" in enforce_src})
    finally:
        srv.shutdown()
        srv.server_close()

    return finish()


def finish() -> int:
    enforced = (
        RESULTS.get("effect_enforcement_point_present", False)
        and RESULTS.get("effect_is_the_discriminator", False)
        and RESULTS.get("effect_semantics_on_enforcement_path", False)
        and RESULTS.get("control_decline_is_unrelated_reason", False)
    )
    verdict = "ENFORCED" if enforced else "FALSIFIER_FIRED"
    print(json.dumps({
        "gate": "G3_effect_semantics",
        "verdict": verdict,
        "checks": RESULTS,
        "details": DETAILS,
        "finding": (
            "OK — mechanism declines a mutating POST substitution with "
            "reason=effect_mismatch; the effect (POST vs GET on the same "
            "recognized endpoint) is the proven discriminator."
            if enforced else
            "DEFECT — no effect-semantics enforcement point: the mechanism "
            "would substitute the read-only hmp-healthcheck harness for a "
            "mutating POST /health (silently changing what the operation does), "
            "or declined for an unrelated reason. Gate-1 NARROW/REWORK candidate."
        ),
    }, indent=2, sort_keys=True))
    return 0 if enforced else 1


def main() -> int:
    tmp_home = Path(tempfile.mkdtemp(prefix="rebar-g3-home-"))
    try:
        return run(tmp_home)
    finally:
        shutil.rmtree(tmp_home, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
