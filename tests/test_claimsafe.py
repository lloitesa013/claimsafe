import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

from claimsafe.contract import default_contract, validate_contract, write_default_contract
from claimsafe.evidence import pack_evidence, write_json
from claimsafe.replay import run_replay
from claimsafe.verifier import verify_packet
from ops.build_claimsafe_stock_example import build_claimsafe_stock_example
from ops.run_claimsafe_demo import run_claimsafe_demo


class ClaimSafeTests(unittest.TestCase):
    def test_init_contract_is_valid(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "claim_contract.json"
            payload = write_default_contract(path, "demo_claim_v0_1")
            self.assertTrue(path.is_file())
            self.assertTrue(validate_contract(payload)["passed"])

    def test_pack_and_verify_clean_packet(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract = default_contract("clean_claim_v0_1")
            contract["required_evidence"] = ["release_gate.json", "replay_result.json"]
            contract_path = root / "claim_contract.json"
            write_json(contract_path, contract)
            write_json(root / "release_gate.json", {"schema": "demo_gate", "status": "passed"})
            write_json(root / "replay_result.json", {"schema": "claimsafe_replay_result_v0_1", "status": "passed"})

            manifest = pack_evidence(
                contract_path,
                [str(root / "release_gate.json"), str(root / "replay_result.json")],
                root / "packet",
            )
            self.assertEqual(manifest["status"], "passed")
            result = verify_packet(root / "packet")
            self.assertTrue(result["publishable"])

    def test_verify_fails_on_missing_required_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract = default_contract("missing_claim_v0_1")
            contract["required_evidence"] = ["release_gate.json", "replay_result.json"]
            contract_path = root / "claim_contract.json"
            write_json(contract_path, contract)
            write_json(root / "release_gate.json", {"status": "passed"})

            pack_evidence(contract_path, [str(root / "release_gate.json")], root / "packet")
            result = verify_packet(root / "packet")
            self.assertFalse(result["publishable"])
            self.assertIn("replay_result.json", result["checks"]["required_evidence"]["missing"])

    def test_verify_fails_on_hash_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract = default_contract("hash_claim_v0_1")
            contract["required_evidence"] = ["release_gate.json", "replay_result.json"]
            contract_path = root / "claim_contract.json"
            write_json(contract_path, contract)
            write_json(root / "release_gate.json", {"status": "passed"})
            write_json(root / "replay_result.json", {"status": "passed"})

            pack_evidence(
                contract_path,
                [str(root / "release_gate.json"), str(root / "replay_result.json")],
                root / "packet",
            )
            (root / "packet" / "release_gate.json").write_text('{"status":"failed"}\n', encoding="utf-8")
            result = verify_packet(root / "packet")
            self.assertFalse(result["checks"]["hashes"]["passed"])
            self.assertFalse(result["publishable"])

    def test_verify_fails_on_forbidden_phrase(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract = default_contract("overclaim_v0_1")
            contract["positive_claim"] = "This includes future return guaranteed behavior."
            contract["required_evidence"] = ["release_gate.json", "replay_result.json"]
            contract_path = root / "claim_contract.json"
            write_json(contract_path, contract)
            write_json(root / "release_gate.json", {"status": "passed"})
            write_json(root / "replay_result.json", {"status": "passed"})

            pack_evidence(
                contract_path,
                [str(root / "release_gate.json"), str(root / "replay_result.json")],
                root / "packet",
            )
            result = verify_packet(root / "packet")
            self.assertFalse(result["checks"]["forbidden_phrases"]["passed"])
            self.assertFalse(result["publishable"])

    def test_replay_records_pass_and_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract = default_contract("replay_claim_v0_1")
            contract["replay_commands"] = [
                {
                    "name": "pass",
                    "command": [sys.executable, "-c", "print('ok')"],
                    "expected_returncode": 0,
                }
            ]
            contract_path = root / "claim_contract.json"
            write_json(contract_path, contract)
            passed = run_replay(contract_path, root / "replay_result.json", cwd=root)
            self.assertEqual(passed["status"], "passed")

            contract["replay_commands"] = [
                {
                    "name": "fail",
                    "command": [sys.executable, "-c", "import sys; sys.exit(7)"],
                    "expected_returncode": 0,
                }
            ]
            write_json(contract_path, contract)
            failed = run_replay(contract_path, root / "replay_result_failed.json", cwd=root)
            self.assertEqual(failed["status"], "failed")

    def test_stock_harness_example_contract_preserves_non_claims(self):
        path = Path(__file__).resolve().parents[1] / "claimsafe" / "examples" / "stock_harness" / "claim_contract.json"
        with path.open("r", encoding="utf-8") as handle:
            contract = json.load(handle)
        self.assertTrue(validate_contract(contract)["passed"])
        self.assertIn("No financial advice.", contract["non_claims"])
        self.assertIn("No return guarantee or future performance claim.", contract["non_claims"])

    def test_demo_exercises_pass_and_failure_modes(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = run_claimsafe_demo(Path(tmp) / "claimsafe_demo", clean=False)
        self.assertEqual(report["status"], "passed")
        self.assertTrue(report["cases"]["clean_pass"])
        self.assertTrue(report["cases"]["overclaim_fails"])
        self.assertTrue(report["cases"]["hash_mismatch_fails"])
        self.assertTrue(report["cases"]["replay_result_fails"])
        self.assertTrue(report["cases"]["replay_command_fails"])

    def test_stock_harness_sample_packet_is_publishable(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = build_claimsafe_stock_example(Path("claimsafe/examples/stock_harness/claim_contract.json"), Path(tmp) / "packet", sample=True)
        self.assertEqual(report["data_mode"], "sample_artifacts")
        self.assertEqual(report["status"], "passed")
        self.assertTrue(report["verification"]["publishable"])


if __name__ == "__main__":
    unittest.main()
