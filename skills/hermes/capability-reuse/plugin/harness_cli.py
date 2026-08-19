from __future__ import annotations

"""Deterministic CLI entrypoints for reviewed Rebar harnesses."""

import argparse
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

try:
    from . import dispatcher
except Exception:  # standalone execution from the plugin directory
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import dispatcher


def _test_override(name: str) -> str:
    if os.environ.get("CAPABILITY_REUSE_TEST_MODE") != "1":
        return ""
    return os.environ.get(name, "").strip()


def _probe_override(peer: str, url: str, timeout_seconds: int) -> dict[str, Any]:
    started = time.monotonic()
    try:
        request = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            body = response.read(65536)
            status_code = getattr(response, "status", 200)
        parsed = json.loads(body.decode("utf-8", "replace"))
        healthy = status_code == 200 and isinstance(parsed, dict) and parsed.get("status") in {"ok", "healthy"}
        return {
            "peer": peer,
            "status": "ok" if healthy else "error",
            "latency_ms": round((time.monotonic() - started) * 1000, 2),
            "error": None if healthy else f"http_{status_code}",
            "detail": parsed,
        }
    except urllib.error.HTTPError as exc:
        return {"peer": peer, "status": "error", "latency_ms": None, "error": f"http_{exc.code}"}
    except Exception as exc:
        text = str(exc).lower()
        code = "timeout" if "timed out" in text else "unavailable"
        return {"peer": peer, "status": "timeout" if code == "timeout" else "error", "latency_ms": None, "error": code}


def hmp_healthcheck(inputs: dict[str, Any]) -> dict[str, Any]:
    override = _test_override("HMP_HEALTH_TARGET_OVERRIDE")
    if not override:
        return dispatcher.hmp_healthcheck(inputs)
    peers = inputs.get("peer_list") if isinstance(inputs, dict) else None
    timeout = inputs.get("timeout_seconds", 5) if isinstance(inputs, dict) else 5
    if not isinstance(peers, list) or len(peers) != 1:
        return {"success": False, "error": "invalid_input", "output": None}
    row = _probe_override(str(peers[0]), override, int(timeout))
    return {
        "success": row.get("status") == "ok",
        "error": row.get("error"),
        "output": [row],
    }


def hmp_send(inputs: dict[str, Any]) -> dict[str, Any]:
    """Sandbox-only HMP send harness until the mutating contract is reviewed."""
    endpoint = _test_override("HMP_SEND_TARGET_OVERRIDE")
    if not endpoint or os.environ.get("CAPABILITY_REUSE_ALLOW_SANDBOX_MUTATING") != "1":
        return {"success": False, "error": "sandbox_override_required", "output": None}
    if not isinstance(inputs, dict):
        return {"success": False, "error": "invalid_input", "output": None}
    peer = inputs.get("peer")
    text = inputs.get("text")
    session_id = inputs.get("session_id", "")
    if not isinstance(peer, str) or not peer or not isinstance(text, str) or not text or len(text) > 2000:
        return {"success": False, "error": "invalid_input", "output": None}
    from_peer = os.environ.get("HMP_FROM_PEER", "peer128").strip() or "peer128"
    digest_input = "\x1f".join((from_peer, peer, text, str(session_id)))
    idempotency_key = "rebar_" + hashlib.sha256(digest_input.encode("utf-8")).hexdigest()[:32]
    body = {
        "from_peer": from_peer,
        "to_peer": peer,
        "session_id": str(session_id),
        "text": text,
        "idempotency_key": idempotency_key,
        "traffic_type": "calibration_probe",
        "operator_solicited": True,
    }
    encoded = json.dumps(body, ensure_ascii=False, sort_keys=True).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=encoded,
        method="POST",
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            response_body = response.read(65536)
            status_code = getattr(response, "status", 200)
        parsed = json.loads(response_body.decode("utf-8", "replace"))
    except urllib.error.HTTPError as exc:
        return {"success": False, "error": f"http_{exc.code}", "output": None}
    except Exception as exc:
        code = "peer_offline_before_send" if "refused" in str(exc).lower() else "unavailable"
        return {"success": False, "error": code, "output": None}
    accepted = status_code in {200, 201, 202} and isinstance(parsed, dict) and parsed.get("accepted") is True
    if not accepted:
        return {"success": False, "error": f"http_{status_code}", "output": parsed}
    return {
        "success": True,
        "error": None,
        "output": {
            "status": str(parsed.get("status") or "accepted"),
            "channel": "hmp",
            "response": str(parsed.get("message_id") or ""),
            "idempotency_key": idempotency_key,
        },
    }


def _load_payload(path: str) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("payload must be a JSON object")
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("capability", choices=("hmp-healthcheck", "hmp-send"))
    parser.add_argument("--payload-file", required=True)
    args = parser.parse_args(argv)
    try:
        payload = _load_payload(args.payload_file)
        if args.capability == "hmp-healthcheck":
            result = hmp_healthcheck(payload)
        else:
            result = hmp_send(payload)
    except Exception as exc:
        result = {"success": False, "error": "invalid_input", "output": None, "detail": str(exc)}
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result.get("success") else 1


if __name__ == "__main__":
    raise SystemExit(main())
