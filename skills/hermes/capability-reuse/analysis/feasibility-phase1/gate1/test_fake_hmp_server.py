"""Tests for the Gate-1 deterministic fake HMP server (Task G1).

Run: python3 -m unittest test_fake_hmp_server -v

Every endpoint's declared shape is asserted, plus the three stateful
behaviours the falsifiers rely on: POST /health MUTATES, GET /messages/next
CONSUMES (not idempotent), and GET /<peer>/health is BLOCKED (403) when the
peer is in the admin block set. A short slow-delay is used so the timeout
endpoint's shape can be checked without waiting the real 2s.
"""
from __future__ import annotations

import json
import time
import unittest
import urllib.error
import urllib.request

import fake_hmp_server as fh


def _get(url: str):
    with urllib.request.urlopen(url, timeout=10) as r:
        return r.status, json.loads(r.read().decode("utf-8"))


def _post(url: str, payload: dict | None = None):
    data = json.dumps(payload or {}).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST",
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return r.status, json.loads(r.read().decode("utf-8"))


class G1ServerTestCase(unittest.TestCase):
    def setUp(self):
        # tiny slow-delay so /slow-health shape check is fast
        self.srv, self.thread, self.base = fh.serve_in_thread(0, slow_delay=0.05)

    def tearDown(self):
        self.srv.shutdown()
        self.srv.server_close()

    def test_get_health_shape(self):
        code, body = _get(self.base + "/health")
        self.assertEqual(code, 200)
        self.assertEqual(body["status"], "healthy")
        self.assertEqual(body["endpoint"], "health")
        self.assertEqual(body["effect"], "read_only")
        self.assertEqual(body["mutations"], 0)

    def test_post_health_mutates(self):
        _, before = _get(self.base + "/health")
        code, body = _post(self.base + "/health")
        self.assertEqual(code, 200)
        self.assertEqual(body["effect"], "mutated")
        self.assertEqual(body["mutations"], before["mutations"] + 1)
        _, after = _get(self.base + "/health")
        self.assertEqual(after["mutations"], 1, "POST /health must persist a mutation")

    def test_slow_health_shape_and_delay(self):
        t0 = time.monotonic()
        code, body = _get(self.base + "/slow-health")
        elapsed = time.monotonic() - t0
        self.assertEqual(code, 200)
        self.assertEqual(body["endpoint"], "slow-health")
        self.assertTrue(body["delayed"])
        self.assertGreaterEqual(elapsed, 0.05, "slow-health must honour its delay")

    def test_ready_is_distinct_from_health(self):
        code, body = _get(self.base + "/ready")
        self.assertEqual(code, 200)
        self.assertTrue(body["ready"])
        self.assertEqual(body["endpoint"], "ready")
        self.assertNotIn("status", body, "ready must not masquerade as a health shape")

    def test_messages_next_consumes(self):
        # empty queue first
        _, empty = _get(self.base + "/messages/next")
        self.assertIsNone(empty["message"])
        self.assertFalse(empty["consumed"])
        # enqueue two, then consume in order
        _post(self.base + "/admin/state", {"enqueue": ["m1", "m2"]})
        _, first = _get(self.base + "/messages/next")
        self.assertEqual(first["message"], "m1")
        self.assertTrue(first["consumed"])
        self.assertEqual(first["remaining"], 1)
        _, second = _get(self.base + "/messages/next")
        self.assertEqual(second["message"], "m2")
        self.assertEqual(second["remaining"], 0)
        # third call: nothing left → NOT idempotent proof
        _, third = _get(self.base + "/messages/next")
        self.assertIsNone(third["message"])

    def test_admin_state_reports_and_blocks_peer(self):
        code, body = _post(self.base + "/admin/state",
                           {"blocked_peers": ["peer-blocked"], "state_token": "S1"})
        self.assertEqual(code, 200)
        self.assertTrue(body["ok"])
        self.assertEqual(body["state"]["blocked_peers"], ["peer-blocked"])
        self.assertEqual(body["state"]["state_token"], "S1")

    def test_blocked_peer_health_returns_403(self):
        _post(self.base + "/admin/state", {"blocked_peers": ["peer-blocked"]})
        try:
            _get(self.base + "/peer-blocked/health")
            self.fail("expected HTTP 403 for blocked peer")
        except urllib.error.HTTPError as e:
            self.assertEqual(e.code, 403)
            body = json.loads(e.read().decode("utf-8"))
            self.assertTrue(body["blocked"])
            self.assertEqual(body["peer"], "peer-blocked")

    def test_unblocked_peer_health_ok(self):
        code, body = _get(self.base + "/peer-ok/health")
        self.assertEqual(code, 200)
        self.assertEqual(body["status"], "healthy")
        self.assertEqual(body["peer"], "peer-ok")

    def test_determinism_same_state_same_body(self):
        # With state unchanged, repeated GET /health bodies are byte-identical.
        _, a = _get(self.base + "/health")
        _, b = _get(self.base + "/health")
        self.assertEqual(json.dumps(a, sort_keys=True), json.dumps(b, sort_keys=True))

    def test_unknown_path_404(self):
        try:
            _get(self.base + "/nope")
            self.fail("expected 404")
        except urllib.error.HTTPError as e:
            self.assertEqual(e.code, 404)


if __name__ == "__main__":
    unittest.main()
