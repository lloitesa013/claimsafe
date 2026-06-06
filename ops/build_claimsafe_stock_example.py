#!/usr/bin/env python3
"""Build the ClaimSafe v0.1 Stock Harness reference packet."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from typing import Iterable, Optional

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from claimsafe.evidence import display_path, pack_evidence  # noqa: E402
from claimsafe.verifier import verify_packet  # noqa: E402

DEFAULT_CONTRACT = Path("claimsafe/examples/stock_harness/claim_contract.json")
DEFAULT_OUTPUT_DIR = Path("dist/claimsafe_stock_harness_packet")
SAMPLE_ARTIFACT_DIR = Path("claimsafe/examples/stock_harness/sample_artifacts")
STOCK_EVIDENCE = [
    (
        "dist/stock_harness_official_claim_packet/OFFICIAL_CLAIM_PACKET_MANIFEST.json",
        "official_claim_packet_manifest.json",
    ),
    ("dist/stock_harness_evidence_packet/EVIDENCE_MANIFEST.json", "stock_harness_evidence_manifest.json"),
    ("reports/stock_harness_release_gate_official.json", "release_gate.json"),
    ("reports/stock_harness_release_candidate_replay_official.json", "replay_result.json"),
]


def _sanitize_stock_artifact(src: Path, dst: Path) -> None:
    text = src.read_text(encoding="utf-8")
    root_posix = str(ROOT).replace("\\", "/")
    wsl_root = root_posix
    if len(root_posix) >= 2 and root_posix[1] == ":":
        drive = root_posix[0].lower()
        wsl_root = "/mnt/" + drive + root_posix[2:]
    replacements = {
        str(ROOT): "<repo-root>",
        str(ROOT).replace("\\", "\\\\"): "<repo-root>",
        root_posix: "<repo-root>",
        wsl_root: "<repo-root>",
    }
    for needle, replacement in replacements.items():
        text = text.replace(needle, replacement)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(text, encoding="utf-8")


def build_claimsafe_stock_example(
    contract_path: Path = DEFAULT_CONTRACT,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    *,
    clean: bool = False,
    sample: bool = False,
    require_real_artifacts: bool = False,
) -> dict:
    contract_path = contract_path if contract_path.is_absolute() else ROOT / contract_path
    output_dir = output_dir if output_dir.is_absolute() else ROOT / output_dir
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        evidence_specs = []
        data_mode = "real_stock_harness_artifacts"
        for src, dst in STOCK_EVIDENCE:
            real_src = ROOT / src
            sample_src = ROOT / SAMPLE_ARTIFACT_DIR / dst
            if sample:
                src_path = sample_src
                data_mode = "sample_artifacts"
            elif real_src.is_file():
                src_path = real_src
            elif require_real_artifacts:
                raise FileNotFoundError("missing Stock Harness evidence artifact: " + str(real_src))
            else:
                src_path = sample_src
                data_mode = "sample_artifacts"
            if not src_path.is_file():
                raise FileNotFoundError("missing ClaimSafe Stock Harness sample artifact: " + str(src_path))
            sanitized = tmp_dir / dst
            _sanitize_stock_artifact(src_path, sanitized)
            evidence_specs.append(str(sanitized) + "=" + dst)
        manifest = pack_evidence(contract_path, evidence_specs, output_dir, clean=clean)
    verification = verify_packet(output_dir)
    return {
        "schema": "claimsafe_stock_harness_example_build_v0_1",
        "status": "passed" if verification.get("publishable") is True else "failed",
        "data_mode": data_mode,
        "output_dir": display_path(output_dir),
        "manifest": manifest,
        "verification": verification,
    }


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Build the ClaimSafe Stock Harness reference packet.")
    parser.add_argument("--contract", default=str(DEFAULT_CONTRACT))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--clean", action="store_true")
    parser.add_argument("--sample", action="store_true", help="Use bundled sanitized sample artifacts.")
    parser.add_argument("--require-real-artifacts", action="store_true", help="Fail instead of falling back to samples.")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args(list(argv) if argv is not None else None)
    report = build_claimsafe_stock_example(
        Path(args.contract),
        Path(args.output_dir),
        clean=args.clean,
        sample=args.sample,
        require_real_artifacts=args.require_real_artifacts,
    )
    print(json.dumps(report, indent=2 if args.pretty else None, sort_keys=True))
    return 0 if report.get("status") == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
