"""Rebar Phase 1 — Gate 1 deterministic fake HMP server (Task G1).

A stdlib-only (`http.server`) fake of the HMP endpoints the Gate-1 falsifiers
(G2..G6) and the structural DEMO (D1) exercise. It is deterministic by design:

  * no randomness, no wall-clock timestamps in any response body;
  * fixed response shapes per endpoint;
  * the ONLY nondeterminism is the explicit, observable server STATE that a
    caller mutates through POST /health, GET /messages/next (consume), and
    POST /admin/state — exactly the behaviours the falsifiers must detect.

Endpoints (frozen plan §4 / Task G1):
  GET  /health            read-only health probe            -> healthy shape
  POST /health            MUTATES (increments a counter)    -> mutated shape
  GET  /slow-health       delayed health probe (timeout)    -> after SLOW_DELAY
  GET  /ready             readiness probe (NOT health)      -> ready shape
  GET  /messages/next     returns AND CONSUMES head msg     -> not idempotent
  POST /admin/state       set state (enqueue / block peers) -> current state
  GET  /<peer>/health     per-peer health; blocked -> 403   -> for G6 policy

The server keeps ALL mutable state on the server instance (not module globals)
so multiple instances in one process stay isolated. It makes no outbound calls
and never imports or touches plugin/ code.

Run standalone:  python3 fake_hmp_server.py --port 8973 --slow-delay 2.0
"""
from __future__ import annotations

import argparse
import json
import os
import threading
import time
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

# Real Gate-1 timeout falsifier (G2) uses a genuinely slow endpoint. The delay
# is configurable ONLY so G1's own shape test need not wait 2 real seconds;
# the default matches the frozen plan (2.0s).
DEFAULT_SLOW_DELAY = float(os.environ.get("FAKE_HMP_SLOW_DELAY", "2.0"))


class _FakeHMPServer(ThreadingHTTPServer):
    """ThreadingHTTPServer carrying per-instance deterministic state."""

    daemon_threads = True

    def __init__(self, addr, handler, slow_delay: float):
        super().__init__(addr, handler)
        self.slow_delay = slow_delay
        # Observable, caller-mutable state (the only source of nondeterminism).
        self.health_mutations = 0          # POST /health count
        self.messages: deque = deque()      # consumed by GET /messages/next
        self.blocked_peers: set[str] = set()  # 403 on GET /<peer>/health
        self.state_token = "S0"            # environmental-state marker (R0a)


class _FakeHMPHandler(BaseHTTPRequestHandler):
    server_version = "FakeHMP/1.0"

    # Silence the default stderr request logging (keeps test output clean).
    def log_message(self, fmt, *args):  # noqa: D401
        return

    # --- helpers ---------------------------------------------------------
    def _send(self, code: int, payload: dict):
        body = json.dumps(payload, sort_keys=True).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self) -> dict:
        length = int(self.headers.get("Content-Length", 0) or 0)
        if not length:
            return {}
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return {}

    def _peer_health(self, peer: str):
        srv = self.server
        if peer in srv.blocked_peers:
            self._send(403, {"blocked": True, "peer": peer, "endpoint": "health"})
            return
        self._send(200, {
            "status": "healthy", "endpoint": "health", "peer": peer,
            "effect": "read_only", "state_token": srv.state_token,
        })

    # --- verbs -----------------------------------------------------------
    def do_GET(self):
        srv = self.server
        path = urlparse(self.path).path.rstrip("/") or "/"

        if path == "/health":
            self._send(200, {
                "status": "healthy", "endpoint": "health", "effect": "read_only",
                "mutations": srv.health_mutations, "state_token": srv.state_token,
            })
        elif path == "/slow-health":
            time.sleep(srv.slow_delay)
            self._send(200, {
                "status": "healthy", "endpoint": "slow-health",
                "delayed": True, "state_token": srv.state_token,
            })
        elif path == "/ready":
            # Readiness is NOT health — distinct endpoint (D1 non-equivalence).
            self._send(200, {
                "ready": True, "endpoint": "ready", "state_token": srv.state_token,
            })
        elif path == "/messages/next":
            # Returns AND consumes: NOT idempotent (G4 duplicate-safety).
            if srv.messages:
                msg = srv.messages.popleft()
                self._send(200, {
                    "message": msg, "consumed": True,
                    "remaining": len(srv.messages),
                })
            else:
                self._send(200, {
                    "message": None, "consumed": False, "remaining": 0,
                })
        elif path.endswith("/health") and path.count("/") == 2:
            peer = path.split("/")[1]
            self._peer_health(peer)
        else:
            self._send(404, {"error": "not_found", "path": path})

    def do_POST(self):
        srv = self.server
        path = urlparse(self.path).path.rstrip("/") or "/"
        body = self._read_body()

        if path == "/health":
            # POST mutates (effect_class differs from GET) — G3 effect semantics.
            srv.health_mutations += 1
            self._send(200, {
                "status": "healthy", "endpoint": "health", "effect": "mutated",
                "mutations": srv.health_mutations, "state_token": srv.state_token,
            })
        elif path == "/admin/state":
            # Deterministic state control: enqueue messages, block peers, set token.
            if "enqueue" in body:
                items = body["enqueue"]
                if isinstance(items, list):
                    srv.messages.extend(items)
                else:
                    srv.messages.append(items)
            if "blocked_peers" in body and isinstance(body["blocked_peers"], list):
                srv.blocked_peers = set(body["blocked_peers"])
            if "state_token" in body:
                srv.state_token = str(body["state_token"])
            self._send(200, {
                "ok": True,
                "state": {
                    "health_mutations": srv.health_mutations,
                    "messages_pending": len(srv.messages),
                    "blocked_peers": sorted(srv.blocked_peers),
                    "state_token": srv.state_token,
                },
            })
        else:
            self._send(404, {"error": "not_found", "path": path})


def make_server(port: int = 0, slow_delay: float | None = None) -> _FakeHMPServer:
    """Create (but do not start) a fake HMP server. port=0 → ephemeral port."""
    delay = DEFAULT_SLOW_DELAY if slow_delay is None else float(slow_delay)
    return _FakeHMPServer(("127.0.0.1", port), _FakeHMPHandler, delay)


def serve_in_thread(port: int = 0, slow_delay: float | None = None):
    """Start the server on a background thread.

    Returns (server, thread, base_url). Caller must server.shutdown() when done.
    """
    srv = make_server(port, slow_delay)
    thread = threading.Thread(target=srv.serve_forever, daemon=True)
    thread.start()
    host, real_port = srv.server_address
    return srv, thread, f"http://{host}:{real_port}"


def _cli(argv=None) -> int:
    p = argparse.ArgumentParser(description="Rebar Gate-1 fake HMP server (G1)")
    p.add_argument("--port", type=int, default=8973)
    p.add_argument("--slow-delay", type=float, default=DEFAULT_SLOW_DELAY)
    ns = p.parse_args(argv)
    srv = make_server(ns.port, ns.slow_delay)
    host, port = srv.server_address
    print(f"fake HMP server on http://{host}:{port} (slow_delay={srv.slow_delay}s)")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
