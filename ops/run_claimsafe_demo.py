#!/usr/bin/env python3
"""Run the ClaimSafe v0.1 pass/fail demo packets."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from claimsafe.contract import default_contract  # noqa: E402
from claimsafe.evidence import display_path, pack_evidence, write_json  # noqa: E402
from claimsafe.replay import run_replay  # noqa: E402
from claimsafe.verifier import verify_packet  # noqa: E402

DEFAULT_OUTPUT_DIR = Path("dist/claimsafe_demo")


def _safe_clean(output_dir: Path) -> None:
    resolved = output_dir.resolve()
    dist_root = (ROOT / "dist").resolve()
    if not str(resolved).startswith(str(dist_root)) or resolved.name != "claimsafe_demo":
        raise ValueError("refusing to clean unexpected output directory: " + str(resolved))
    if resolved.exists():
        shutil.rmtree(str(resolved))


def _write_contract(path: Path, claim_id: str, *, overclaim: bool = False, replay_commands: bool = False) -> Dict[str, Any]:
    contract = default_contract(claim_id)
    contract["positive_claim"] = "This packet demonstrates bounded AI claim verification."
    if overclaim:
        contract["positive_claim"] = "This AI has guaranteed returns for the future."
    contract["required_evidence"] = ["release_gate.json", "replay_result.json"]
    contract["non_claims"] = [
        "No future performance guarantee.",
        "No live deployment readiness claim.",
        "No claim outside the included evidence packet.",
    ]
    if replay_commands:
        contract["replay_commands"] = [
            {
                "name": "intentional_replay_failure",
                "command": [sys.executable, "-c", "import sys; sys.exit(7)"],
                "expected_returncode": 0,
            }
        ]
    write_json(path, contract)
    return contract


def _build_packet(work_dir: Path, packet_dir: Path, claim_id: str, *, overclaim: bool = False, replay_failed: bool = False) -> Dict[str, Any]:
    work_dir.mkdir(parents=True, exist_ok=True)
    contract_path = work_dir / "claim_contract.json"
    _write_contract(contract_path, claim_id, overclaim=overclaim)
    write_json(work_dir / "release_gate.json", {"schema": "claimsafe_demo_release_gate_v0_1", "status": "passed"})
    write_json(
        work_dir / "replay_result.json",
        {"schema": "claimsafe_demo_replay_result_v0_1", "status": "failed" if replay_failed else "passed"},
    )
    manifest = pack_evidence(
        contract_path,
        [str(work_dir / "release_gate.json"), str(work_dir / "replay_result.json")],
        packet_dir,
        clean=True,
    )
    verification = verify_packet(packet_dir)
    return {"manifest": manifest, "verification": verification}


def run_claimsafe_demo(output_dir: Path = DEFAULT_OUTPUT_DIR, *, clean: bool = False) -> Dict[str, Any]:
    output_dir = output_dir if output_dir.is_absolute() else ROOT / output_dir
    if clean:
        _safe_clean(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    clean_case = _build_packet(
        output_dir / "work" / "clean",
        output_dir / "packets" / "clean",
        "claimsafe_demo_clean_v0_1",
    )
    overclaim_case = _build_packet(
        output_dir / "work" / "overclaim",
        output_dir / "packets" / "overclaim",
        "claimsafe_demo_overclaim_v0_1",
        overclaim=True,
    )
    hash_case = _build_packet(
        output_dir / "work" / "hash_mismatch",
        output_dir / "packets" / "hash_mismatch",
        "claimsafe_demo_hash_mismatch_v0_1",
    )
    (output_dir / "packets" / "hash_mismatch" / "release_gate.json").write_text(
        '{"schema":"claimsafe_demo_release_gate_v0_1","status":"failed"}\n',
        encoding="utf-8",
    )
    hash_case["verification_after_tamper"] = verify_packet(output_dir / "packets" / "hash_mismatch")

    replay_case = _build_packet(
        output_dir / "work" / "replay_failed",
        output_dir / "packets" / "replay_failed",
        "claimsafe_demo_replay_failed_v0_1",
        replay_failed=True,
    )

    replay_command_dir = output_dir / "work" / "replay_command_failed"
    replay_command_dir.mkdir(parents=True, exist_ok=True)
    replay_contract_path = replay_command_dir / "claim_contract.json"
    _write_contract(
        replay_contract_path,
        "claimsafe_demo_replay_command_failed_v0_1",
        replay_commands=True,
    )
    replay_command_result = run_replay(
        replay_contract_path,
        replay_command_dir / "replay_result.json",
        cwd=replay_command_dir,
    )

    cases = {
        "clean_pass": clean_case["verification"].get("publishable") is True,
        "overclaim_fails": overclaim_case["verification"].get("publishable") is False
        and overclaim_case["verification"]["checks"]["forbidden_phrases"]["passed"] is False,
        "hash_mismatch_fails": hash_case["verification_after_tamper"].get("publishable") is False
        and hash_case["verification_after_tamper"]["checks"]["hashes"]["passed"] is False,
        "replay_result_fails": replay_case["verification"].get("publishable") is False
        and replay_case["verification"]["checks"]["replay"]["passed"] is False,
        "replay_command_fails": replay_command_result.get("status") == "failed",
    }
    report = {
        "schema": "claimsafe_demo_report_v0_1",
        "status": "passed" if all(cases.values()) else "failed",
        "output_dir": display_path(output_dir),
        "cases": cases,
        "packets": {
            "clean": display_path(output_dir / "packets" / "clean"),
            "overclaim": display_path(output_dir / "packets" / "overclaim"),
            "hash_mismatch": display_path(output_dir / "packets" / "hash_mismatch"),
            "replay_failed": display_path(output_dir / "packets" / "replay_failed"),
        },
        "replay_command_result": replay_command_result,
    }
    write_json(output_dir / "claimsafe_demo_report.json", report)
    return report


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run the ClaimSafe v0.1 demo.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--clean", action="store_true")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args(list(argv) if argv is not None else None)
    report = run_claimsafe_demo(Path(args.output_dir), clean=args.clean)
    print(json.dumps(report, indent=2 if args.pretty else None, sort_keys=True))
    return 0 if report.get("status") == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
