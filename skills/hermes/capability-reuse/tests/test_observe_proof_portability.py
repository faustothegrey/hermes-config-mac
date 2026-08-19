from pathlib import Path
import unittest


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"


class ObserveProofPortabilityTests(unittest.TestCase):
    def test_real_gateway_proof_resolves_runtime_from_home(self):
        source = (SCRIPTS_DIR / "observe-channel-real-gateway-dispatch-proof.py").read_text()
        self.assertNotIn('"/home/fausto/.hermes/plugins/capability-reuse"', source)
        self.assertIn("Path.home()", source)


if __name__ == "__main__":
    unittest.main()
