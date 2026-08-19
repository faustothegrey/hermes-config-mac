"""Tests for the A5 material-change log (Task M1).

Run: python3 -m unittest test_material_change_log -v
Each test runs in an isolated M1_DIR so the real log is never touched.
"""
from __future__ import annotations

import importlib
import os
import tempfile
import unittest


class M1TestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        os.environ["M1_DIR"] = self._tmp.name
        # import fresh so module-level paths pick up M1_DIR at call time
        self.m1 = importlib.import_module("material_change_log")
        importlib.reload(self.m1)

    def tearDown(self):
        os.environ.pop("M1_DIR", None)
        self._tmp.cleanup()

    def test_init_records_start_timestamp(self):
        meta = self.m1.init()
        self.assertIn("log_started_at", meta)
        self.assertEqual(meta["schema"], self.m1.SCHEMA)

    def test_second_init_without_force_refuses(self):
        self.m1.init()
        with self.assertRaises(SystemExit):
            self.m1.init()

    def test_append_before_init_raises(self):
        with self.assertRaises(RuntimeError):
            self.m1.append("normalizer", True, "should fail, not initialized")

    def test_append_valid_record(self):
        self.m1.init()
        rec = self.m1.append("comparator", False, "tolerance tweak, no semantics change")
        self.assertEqual(rec["component"], "comparator")
        self.assertFalse(rec["material"])
        self.assertEqual(len(self.m1._read_entries()), 1)

    def test_append_invalid_component_raises(self):
        self.m1.init()
        with self.assertRaises(ValueError):
            self.m1.append("retriever", True, "not one of the three components")

    def test_append_empty_rationale_raises(self):
        self.m1.init()
        with self.assertRaises(ValueError):
            self.m1.append("normalizer", True, "   ")

    def test_ratchet_upgrade_allowed(self):
        self.m1.init()
        self.m1.append("normalizer", False, "thought cosmetic", entry_id="mc-0001")
        self.m1.reclassify("mc-0001", True, "review found it changes normalized op")
        self.assertTrue(self.m1.effective_material("mc-0001"))

    def test_ratchet_downgrade_forbidden(self):
        self.m1.init()
        self.m1.append("capability", True, "contract semantics changed", entry_id="mc-0001")
        with self.assertRaises(ValueError):
            self.m1.reclassify("mc-0001", False, "trying to rescue the window")

    def test_append_only_history_preserved_after_amendment(self):
        self.m1.init()
        self.m1.append("normalizer", False, "initial call", entry_id="mc-0001")
        self.m1.reclassify("mc-0001", True, "upgraded")
        entries = self.m1._read_entries()
        # original record still present, unmutated
        original = next(e for e in entries if e["id"] == "mc-0001")
        self.assertFalse(original["material"])
        # amendment appended separately
        self.assertTrue(any(e.get("amends") == "mc-0001" for e in entries))


if __name__ == "__main__":
    unittest.main()
