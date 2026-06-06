from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional

from .contract import load_contract
from .evidence import display_path, write_json


def _display_command(command: List[str]) -> List[str]:
    displayed: List[str] = []
    cwd = Path.cwd().resolve()
    for part in command:
        try:
            path = Path(part)
            if path.is_absolute():
                displayed.append(display_path(path.resolve()))
                continue
        except (OSError, ValueError):
            pass
        displayed.append(part)
    return displayed


def _run_command(command_spec: Mapping[str, Any], base_cwd: Path) -> Dict[str, Any]:
    name = str(command_spec.get("name", "command"))
    command = command_spec.get("command", [])
    cwd_value = command_spec.get("cwd")
    cwd = (base_cwd / cwd_value).resolve() if isinstance(cwd_value, str) else base_cwd
    expected = int(command_spec.get("expected_returncode", 0))
    started = time.time()
    if not isinstance(command, list) or not all(isinstance(part, str) for part in command):
        return {
            "name": name,
            "command": command,
            "returncode": None,
            "elapsed_seconds": 0.0,
            "stdout_tail": "",
            "stderr_tail": "command must be a string array",
            "passed": False,
        }
    try:
        completed = subprocess.run(
            command,
            cwd=str(cwd),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            check=False,
        )
        return {
            "name": name,
            "command": _display_command(command),
            "cwd": display_path(cwd),
            "returncode": completed.returncode,
            "expected_returncode": expected,
            "elapsed_seconds": round(time.time() - started, 6),
            "stdout_tail": completed.stdout[-4000:],
            "stderr_tail": completed.stderr[-4000:],
            "passed": completed.returncode == expected,
        }
    except OSError as exc:
        return {
            "name": name,
            "command": _display_command(command),
            "cwd": display_path(cwd),
            "returncode": None,
            "expected_returncode": expected,
            "elapsed_seconds": round(time.time() - started, 6),
            "stdout_tail": "",
            "stderr_tail": str(exc),
            "passed": False,
        }


def run_replay(contract_path: Path, output_path: Path, *, cwd: Optional[Path] = None) -> Dict[str, Any]:
    contract_path = contract_path.resolve()
    base_cwd = cwd.resolve() if cwd is not None else contract_path.parent.resolve()
    contract = load_contract(contract_path)
    commands = contract.get("replay_commands", [])
    command_results = [_run_command(command, base_cwd) for command in commands if isinstance(command, dict)]
    checks = {
        "replay_commands_present": bool(commands),
        "all_commands_passed": bool(command_results) and all(result.get("passed") for result in command_results),
    }
    result = {
        "schema": "claimsafe_replay_result_v0_1",
        "status": "passed" if all(checks.values()) else "failed",
        "generated_at_unix": int(time.time()),
        "claim_id": contract.get("claim_id"),
        "checks": checks,
        "commands": command_results,
    }
    write_json(output_path, result)
    return result
