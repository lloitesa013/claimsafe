from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable, Optional

from .contract import write_default_contract
from .evidence import pack_evidence
from .replay import run_replay
from .verifier import verify_packet


def _print(payload, pretty: bool) -> None:
    print(json.dumps(payload, indent=2 if pretty else None, sort_keys=True))


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="ClaimSafe v0.1 release gate for bounded AI claims.")
    parser.add_argument("--pretty", action="store_true", help="Print indented JSON.")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="Create a claim contract template.")
    init.add_argument("--claim-id", required=True)
    init.add_argument("--output", default="claim_contract.json")
    init.add_argument("--overwrite", action="store_true")

    pack = sub.add_parser("pack", help="Build an evidence packet.")
    pack.add_argument("--contract", required=True)
    pack.add_argument("--evidence", action="append", default=[], help="Evidence path or source=dest mapping.")
    pack.add_argument("--output-dir", default="dist/claimsafe_packet")
    pack.add_argument("--clean", action="store_true")

    verify = sub.add_parser("verify", help="Verify an evidence packet.")
    verify.add_argument("--packet-dir", default="dist/claimsafe_packet")

    replay = sub.add_parser("replay", help="Run replay commands from a contract.")
    replay.add_argument("--contract", required=True)
    replay.add_argument("--output", default="replay_result.json")
    replay.add_argument("--cwd")

    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.command == "init":
        payload = write_default_contract(Path(args.output), args.claim_id, overwrite=args.overwrite)
        _print(payload, args.pretty)
        return 0
    if args.command == "pack":
        payload = pack_evidence(Path(args.contract), args.evidence, Path(args.output_dir), clean=args.clean)
        _print(payload, args.pretty)
        return 0 if payload.get("status") == "passed" else 1
    if args.command == "verify":
        payload = verify_packet(Path(args.packet_dir))
        _print(payload, args.pretty)
        return 0 if payload.get("publishable") is True else 1
    if args.command == "replay":
        cwd = Path(args.cwd) if args.cwd else None
        payload = run_replay(Path(args.contract), Path(args.output), cwd=cwd)
        _print(payload, args.pretty)
        return 0 if payload.get("status") == "passed" else 1
    return 2

