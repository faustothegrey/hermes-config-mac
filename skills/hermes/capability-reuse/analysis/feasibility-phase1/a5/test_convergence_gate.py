"""Tests for the A5 convergence gate (Task M2).

Run: python3 -m unittest test_convergence_gate -v
Isolated M1_DIR per test — the real material-change log is never touched.
"""
from __future__ import annotations

import datetime
import importlib
import os
import tempfile
import unittest


def _iso(offset_seconds: int = 0) -> str:
    return (datetime.datetime.now(datetime.timezone.utc)
            + datetime.timedelta(seconds=offset_seconds)).isoformat()


class M2TestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        os.environ["M1_DIR"] = self._tmp.name
        self.m1 = importlib.import_module("material_change_log")
        importlib.reload(self.m1)
        self.m2 = importlib.import_module("convergence_gate")
        importlib.reload(self.m2)
        self.m1.init()

    def tearDown(self):
        os.environ.pop("M1_DIR", None)
        self._tmp.cleanup()

    def test_empty_log_window_is_converged(self):
        res = self.m2.evaluate_window(_iso(-100), None)
        self.assertTrue(res["converged"])
        self.assertEqual(res["voided_by"], [])

    def test_non_material_change_does_not_void(self):
        self.m1.append("comparator", False, "cosmetic rename")
        res = self.m2.evaluate_window(_iso(-100), None)
        self.assertTrue(res["converged"])

    def test_material_change_inside_window_voids_it(self):
        self.m1.append("normalizer", True, "changes normalized op")
        res = self.m2.evaluate_window(_iso(-100), None)
        self.assertFalse(res["converged"])
        self.assertEqual(len(res["voided_by"]), 1)
        self.assertEqual(res["voided_by"][0]["component"], "normalizer")

    def test_material_change_before_window_does_not_void(self):
        # change happens "now"; window starts in the future → change is before it
        self.m1.append("capability", True, "contract change before window")
        res = self.m2.evaluate_window(_iso(+50), _iso(+100))
        self.assertTrue(res["converged"])

    def test_ratchet_upgrade_voids_previously_clean_window(self):
        # entry logged as non-material, later upgraded to material by review
        self.m1.append("comparator", False, "thought cosmetic", entry_id="mc-0001")
        clean = self.m2.evaluate_window(_iso(-100), None)
        self.assertTrue(clean["converged"])
        self.m1.reclassify("mc-0001", True, "review: changes equivalence class")
        after = self.m2.evaluate_window(_iso(-100), None)
        self.assertFalse(after["converged"])

    def test_any_of_three_components_voids(self):
        for comp in ("normalizer", "capability", "comparator"):
            with self.subTest(comp=comp):
                # fresh log per subtest
                self.m1.init(force=True)
                self.m1.append(comp, True, f"{comp} material change")
                res = self.m2.evaluate_window(_iso(-100), None)
                self.assertFalse(res["converged"])

    def test_gate_never_mutates_m1_log(self):
        # Integrity: evaluating a window is READ-ONLY over the M1 log.
        import hashlib
        self.m1.append("normalizer", True, "some change")
        log_path = self.m1._log_path()
        before = hashlib.sha256(log_path.read_bytes()).hexdigest()
        self.m2.evaluate_window(_iso(-100), None)
        self.m2.evaluate_window(_iso(-100), _iso(+100))
        after = hashlib.sha256(log_path.read_bytes()).hexdigest()
        self.assertEqual(before, after, "convergence gate must not mutate the M1 log")

    def test_stable_window_after_last_material_change_converges(self):
        # A material change, then a later window that starts AFTER it → stable.
        self.m1.append("capability", True, "contract change")
        res = self.m2.evaluate_window(_iso(+30), _iso(+120))
        self.assertTrue(res["converged"])
        self.assertEqual(res["voided_by"], [])


if __name__ == "__main__":
    unittest.main()
