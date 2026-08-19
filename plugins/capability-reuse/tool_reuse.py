from __future__ import annotations

"""Operation-specific Rebar decisions at the real tool boundary."""

import ast
import copy
import hashlib
import json
import os
import shlex
import sys
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

try:
    from .execution_plan import PEER_MAP
    from . import compatibility
    from . import event_store as events
    from . import registry
except Exception:  # pragma: no cover - standalone harness imports
    from execution_plan import PEER_MAP
    import compatibility
    import event_store as events
    import registry


@dataclass(frozen=True)
class OperationAnalysis:
    status: str
    operation_kind: str = ""
    effect_class: str = ""
    target: str = ""
    inputs: dict[str, Any] = field(default_factory=dict)
    reason: str = ""


@dataclass(frozen=True)
class HarnessDecision:
    outcome: str
    reason: str
    capability_id: str = ""
    capability_version: str = ""
    operation_kind: str = ""
    inputs: dict[str, Any] = field(default_factory=dict)
    will_rewrite: bool = False


_OPERATION_CAPABILITIES = {
    "hmp.health": ("hmp-healthcheck", "1.0.0"),
    "hmp.send": ("hmp-send", "1.0.0"),
}
_GENERIC_TOOL_SURFACES = {"terminal", "execute_code"}
_decision_lock = threading.Lock()
_decisions_by_tool_call: dict[str, dict[str, Any]] = {}
_DECISION_TTL_SECONDS = 900.0


def _csv_env(name: str) -> list[str]:
    return [part.strip() for part in os.environ.get(name, "").split(",") if part.strip()]


def _peer_for_host(host: str) -> str:
    host = (host or "").strip().lower()
    for peer, (ip, _path) in PEER_MAP.items():
        if host in {peer.lower(), str(ip).lower()}:
            return peer
    return ""


def _derive_execute_code(args: dict[str, Any]) -> OperationAnalysis:
    code = args.get("code")
    if not isinstance(code, str) or not code.strip():
        return OperationAnalysis(status="no_harness", reason="empty_code")
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return OperationAnalysis(status="rejected", reason="unparseable_code")
    calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
    target_calls: list[tuple[ast.Call, str]] = []
    for call in calls:
        function = call.func
        if (
            isinstance(function, ast.Attribute)
            and isinstance(function.value, ast.Name)
            and function.value.id == "requests"
            and function.attr in {"get", "post"}
            and call.args
            and isinstance(call.args[0], ast.Constant)
            and isinstance(call.args[0].value, str)
        ):
            target_calls.append((call, function.attr))
    if not target_calls:
        return OperationAnalysis(status="no_harness", reason="unrecognized_operation")
    if len(target_calls) != 1 or len(calls) != 1:
        return OperationAnalysis(status="rejected", reason="partial_coverage")
    call, method = target_calls[0]
    parsed = urlparse(str(call.args[0].value))
    peer = _peer_for_host(parsed.hostname or "")
    if not peer:
        return OperationAnalysis(status="rejected", reason="unsupported_target")
    path = (parsed.path or "/").rstrip("/") or "/"
    if method == "get" and path in {"/hmp/health", "/health"}:
        timeout = 5
        for keyword in call.keywords:
            if keyword.arg == "timeout" and isinstance(keyword.value, ast.Constant):
                try:
                    timeout = int(float(keyword.value.value))
                except (TypeError, ValueError):
                    return OperationAnalysis(status="rejected", reason="invalid_timeout")
        return OperationAnalysis(
            status="matched",
            operation_kind="hmp.health",
            effect_class="read_only",
            target=peer,
            inputs={"peer_list": [peer], "timeout_seconds": timeout},
        )
    return OperationAnalysis(status="no_harness", reason="unrecognized_endpoint")


def derive_operation(tool_name: str, args: dict[str, Any] | None) -> OperationAnalysis:
    if tool_name == "execute_code" and isinstance(args, dict):
        return _derive_execute_code(args)
    if tool_name != "terminal" or not isinstance(args, dict):
        return OperationAnalysis(status="no_harness", reason="unsupported_tool")
    command = args.get("command")
    if not isinstance(command, str) or not command.strip():
        return OperationAnalysis(status="no_harness", reason="empty_command")
    try:
        tokens = shlex.split(command, posix=True)
    except ValueError:
        return OperationAnalysis(status="rejected", reason="unparseable_command")
    if not tokens or tokens[0] != "curl":
        return OperationAnalysis(status="no_harness", reason="unrecognized_operation")
    if any(token in {"&&", "||", ";", "|", "&"} for token in tokens):
        return OperationAnalysis(status="rejected", reason="partial_coverage")

    url = next((token for token in tokens[1:] if token.startswith(("http://", "https://"))), "")
    if not url:
        return OperationAnalysis(status="no_harness", reason="missing_url")
    parsed = urlparse(url)
    peer = _peer_for_host(parsed.hostname or "")
    if not peer:
        return OperationAnalysis(status="rejected", reason="unsupported_target")

    path = (parsed.path or "/").rstrip("/") or "/"
    method = "GET"
    data_arg = ""
    for index, token in enumerate(tokens[:-1]):
        if token in {"-X", "--request"}:
            method = str(tokens[index + 1]).upper()
        elif token in {"-d", "--data", "--data-raw", "--data-binary"}:
            data_arg = str(tokens[index + 1])

    if path == "/hmp/send":
        if method != "POST":
            return OperationAnalysis(status="rejected", reason="effect_mismatch")
        if not data_arg:
            return OperationAnalysis(status="rejected", reason="missing_payload")
        if data_arg.startswith("@"):
            return OperationAnalysis(
                status="matched",
                operation_kind="hmp.send",
                effect_class="mutating",
                target=peer,
                inputs={"peer": peer, "payload_file": data_arg[1:]},
            )
        try:
            payload = json.loads(data_arg)
        except (TypeError, json.JSONDecodeError):
            return OperationAnalysis(status="rejected", reason="invalid_payload")
        if not isinstance(payload, dict):
            return OperationAnalysis(status="rejected", reason="invalid_payload")
        requested_peer = str(payload.get("to_peer") or payload.get("to") or peer)
        text = payload.get("text")
        if text is None and isinstance(payload.get("payload"), dict):
            text = payload["payload"].get("message")
        if requested_peer != peer or not isinstance(text, str) or not text:
            return OperationAnalysis(status="rejected", reason="payload_target_mismatch")
        inputs = {"peer": peer, "text": text}
        session_id = payload.get("session_id")
        if isinstance(session_id, str) and session_id:
            inputs["session_id"] = session_id
        return OperationAnalysis(
            status="matched",
            operation_kind="hmp.send",
            effect_class="mutating",
            target=peer,
            inputs=inputs,
        )

    if path not in {"/hmp/health", "/health"}:
        return OperationAnalysis(status="no_harness", reason="unrecognized_endpoint")
    if method not in {"GET", "HEAD"}:
        return OperationAnalysis(status="rejected", reason="effect_mismatch")

    timeout = 5
    for index, token in enumerate(tokens[:-1]):
        if token in {"--max-time", "-m"}:
            try:
                timeout = int(float(tokens[index + 1]))
            except (TypeError, ValueError):
                return OperationAnalysis(status="rejected", reason="invalid_timeout")

    return OperationAnalysis(
        status="matched",
        operation_kind="hmp.health",
        effect_class="read_only",
        target=peer,
        inputs={"peer_list": [peer], "timeout_seconds": timeout},
    )


def decide_operation(analysis: OperationAnalysis) -> HarnessDecision:
    if analysis.status == "no_harness":
        return HarnessDecision(
            outcome="no_harness",
            reason=analysis.reason or "no_compatible_harness",
            operation_kind=analysis.operation_kind,
            inputs=dict(analysis.inputs),
        )
    if analysis.status != "matched":
        return HarnessDecision(
            outcome="rejected",
            reason=analysis.reason or "operation_rejected",
            operation_kind=analysis.operation_kind,
            inputs=dict(analysis.inputs),
        )

    capability_ref = _OPERATION_CAPABILITIES.get(analysis.operation_kind)
    if not capability_ref:
        return HarnessDecision(
            outcome="no_harness",
            reason="no_registered_operation_mapping",
            operation_kind=analysis.operation_kind,
            inputs=dict(analysis.inputs),
        )
    capability_id, capability_version = capability_ref
    capability = registry.get_capability(capability_id, capability_version)
    if not capability:
        return HarnessDecision(
            outcome="no_harness",
            reason="capability_not_registered",
            capability_id=capability_id,
            capability_version=capability_version,
            operation_kind=analysis.operation_kind,
            inputs=dict(analysis.inputs),
        )

    contract = capability.get("invocation_contract", {})
    sandbox_send = (
        analysis.operation_kind == "hmp.send"
        and os.environ.get("CAPABILITY_REUSE_TEST_MODE") == "1"
        and os.environ.get("CAPABILITY_REUSE_ALLOW_SANDBOX_MUTATING") == "1"
        and bool(os.environ.get("HMP_SEND_TARGET_OVERRIDE", "").strip())
    )
    if analysis.operation_kind == "hmp.send" and (
        contract.get("effect_class") == "mutating"
        and contract.get("trust_state") != "trusted"
        and not sandbox_send
    ):
        return HarnessDecision(
            outcome="rejected",
            reason="mutating_not_trusted",
            capability_id=capability_id,
            capability_version=capability_version,
            operation_kind=analysis.operation_kind,
            inputs=dict(analysis.inputs),
        )

    capability_for_check = capability
    if sandbox_send:
        capability_for_check = copy.deepcopy(capability)
        capability_for_check.setdefault("invocation_contract", {})["trust_state"] = "trusted"

    compatible = compatibility.check_all(
        capability_for_check,
        request_effect=analysis.effect_class,
        available_permissions=_csv_env("CAPABILITY_REUSE_PERMISSIONS"),
        available_capabilities=_csv_env("CAPABILITY_REUSE_AVAILABLE_CAPABILITIES"),
    )
    if not compatible.compatible:
        return HarnessDecision(
            outcome="rejected",
            reason=compatible.reason or "compatibility_rejected",
            capability_id=capability_id,
            capability_version=capability_version,
            operation_kind=analysis.operation_kind,
            inputs=dict(analysis.inputs),
        )

    active_allowlist = _csv_env("CAPABILITY_REUSE_ACTIVE_CAPABILITIES") or ["hmp-healthcheck"]
    if capability_id not in active_allowlist:
        return HarnessDecision(
            outcome="rejected",
            reason="capability_not_active",
            capability_id=capability_id,
            capability_version=capability_version,
            operation_kind=analysis.operation_kind,
            inputs=dict(analysis.inputs),
        )

    if os.environ.get("CAPABILITY_REUSE_TOOL_REUSE_MODE", "shadow").strip().lower() != "active":
        return HarnessDecision(
            outcome="rejected",
            reason="shadow_mode",
            capability_id=capability_id,
            capability_version=capability_version,
            operation_kind=analysis.operation_kind,
            inputs=dict(analysis.inputs),
        )

    return HarnessDecision(
        outcome="reused",
        reason="sandbox_harness_reuse" if sandbox_send else "harness_reuse",
        capability_id=capability_id,
        capability_version=capability_version,
        operation_kind=analysis.operation_kind,
        inputs=dict(analysis.inputs),
        will_rewrite=True,
    )


def _remember_tool_decision(tool_call_id: str, decision: HarnessDecision, context: dict[str, Any]) -> None:
    if not tool_call_id:
        return
    now = time.monotonic()
    record = {
        "decision": decision,
        "context": dict(context),
        "created_monotonic": now,
    }
    with _decision_lock:
        expired = [
            key for key, value in _decisions_by_tool_call.items()
            if now - float(value.get("created_monotonic", now)) > _DECISION_TTL_SECONDS
        ]
        for key in expired:
            _decisions_by_tool_call.pop(key, None)
        _decisions_by_tool_call[tool_call_id] = record


def clear_tool_decisions() -> None:
    with _decision_lock:
        _decisions_by_tool_call.clear()


def _write_payload_file(tool_call_id: str, payload: dict[str, Any]) -> Path:
    configured = os.environ.get("CAPABILITY_REUSE_HARNESS_INPUT_DIR", "").strip()
    directory = Path(configured) if configured else Path.home() / ".hermes" / "cache" / "rebar-harness-inputs"
    directory.mkdir(parents=True, exist_ok=True)
    safe_id = hashlib.sha256(tool_call_id.encode("utf-8", "replace")).hexdigest()[:24]
    path = directory / f"{safe_id}.json"
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(encoded)
    except Exception:
        try:
            os.close(descriptor)
        except OSError:
            pass
        raise
    os.chmod(path, 0o600)
    return path


def _harness_command(decision: HarnessDecision, payload_path: Path) -> str:
    capability_name = decision.capability_id
    script = Path(__file__).with_name("harness_cli.py")
    return " ".join(
        shlex.quote(part)
        for part in (sys.executable, str(script), capability_name, "--payload-file", str(payload_path))
    )


def on_tool_request(
    tool_name: str,
    args: dict[str, Any],
    original_args: dict[str, Any] | None = None,
    **context: Any,
) -> dict[str, Any] | None:
    """Tool-request middleware: decide from original args and optionally rewrite.

    Any failure is fail-open: the original request is left untouched.
    """
    if tool_name not in _GENERIC_TOOL_SURFACES or not isinstance(args, dict):
        return None
    tool_call_id = str(context.get("tool_call_id") or "")
    try:
        source_args = original_args if isinstance(original_args, dict) else args
        analysis = derive_operation(tool_name, source_args)
        decision = decide_operation(analysis)
        _remember_tool_decision(tool_call_id, decision, context)
        if not decision.will_rewrite:
            return None
        payload_path = _write_payload_file(tool_call_id, decision.inputs)
        rewritten = dict(args)
        rewritten["command"] = _harness_command(decision, payload_path)
        return {
            "args": rewritten,
            "source": "capability-reuse",
            "reason": decision.reason,
            "name": f"{decision.capability_id}@{decision.capability_version}",
        }
    except Exception:
        return None


def consume_tool_decision(tool_call_id: str) -> dict[str, Any] | None:
    if not tool_call_id:
        return None
    with _decision_lock:
        record = _decisions_by_tool_call.pop(tool_call_id, None)
    if not record:
        return None
    decision = record.get("decision")
    if not isinstance(decision, HarnessDecision):
        return None
    decision_context = dict(record.get("context", {}))
    decision_context.setdefault("tool_call_id", tool_call_id)
    try:
        events.emit_harness_decision(
            tool_call_id=tool_call_id,
            outcome=decision.outcome,
            reason=decision.reason,
            capability_id=decision.capability_id,
            capability_version=decision.capability_version,
            operation_kind=decision.operation_kind,
            rewritten=decision.will_rewrite,
            context=decision_context,
        )
    except Exception:
        pass
    capability = (
        f"{decision.capability_id}@{decision.capability_version}"
        if decision.capability_id else ""
    )
    if decision.outcome == "reused":
        return {
            "kind": "matched",
            "text": f"{capability} reused",
            "decision": decision,
            "context": record.get("context", {}),
        }
    if decision.outcome == "rejected":
        label = capability or decision.operation_kind or "candidate"
        return {
            "kind": "rejected",
            "text": f"{label} rejected · {decision.reason}",
            "decision": decision,
            "context": record.get("context", {}),
        }
    return {
        "kind": "generic",
        "text": "checked · no specialized harness",
        "decision": decision,
        "context": record.get("context", {}),
    }
