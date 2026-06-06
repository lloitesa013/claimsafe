from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Tuple

CLAIMSAFE_CONTRACT_SCHEMA = "claimsafe_contract_v0_1"
DEFAULT_PUBLISHABLE_WHEN = [
    "schema_valid",
    "required_evidence_present",
    "hashes_verified",
    "release_gate_passed",
    "replay_passed",
    "non_claims_preserved",
    "forbidden_phrases_absent",
]


def load_contract(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError("claim contract must be a JSON object: " + str(path))
    return payload


def _is_string_list(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) and item.strip() for item in value)


def _validate_replay_commands(commands: Any) -> List[str]:
    errors: List[str] = []
    if commands is None:
        return errors
    if not isinstance(commands, list):
        return ["replay_commands must be a list when present"]
    for index, command in enumerate(commands):
        prefix = "replay_commands[%d]" % index
        if not isinstance(command, dict):
            errors.append(prefix + " must be an object")
            continue
        if not isinstance(command.get("name"), str) or not command.get("name", "").strip():
            errors.append(prefix + ".name must be a non-empty string")
        argv = command.get("command")
        if not _is_string_list(argv):
            errors.append(prefix + ".command must be a non-empty string array")
        cwd = command.get("cwd")
        if cwd is not None and not isinstance(cwd, str):
            errors.append(prefix + ".cwd must be a string when present")
    return errors


def validate_contract(contract: Mapping[str, Any]) -> Dict[str, Any]:
    checks = {
        "schema": contract.get("schema") == CLAIMSAFE_CONTRACT_SCHEMA,
        "claim_id": isinstance(contract.get("claim_id"), str) and bool(contract.get("claim_id", "").strip()),
        "positive_claim": isinstance(contract.get("positive_claim"), str)
        and bool(contract.get("positive_claim", "").strip()),
        "claim_limit": isinstance(contract.get("claim_limit"), str) and bool(contract.get("claim_limit", "").strip()),
        "non_claims": _is_string_list(contract.get("non_claims")),
        "required_evidence": _is_string_list(contract.get("required_evidence")),
        "publishable_when": _is_string_list(contract.get("publishable_when")),
        "forbidden_phrases": (
            "forbidden_phrases" not in contract or _is_string_list(contract.get("forbidden_phrases"))
        ),
    }
    replay_errors = _validate_replay_commands(contract.get("replay_commands"))
    checks["replay_commands"] = replay_errors == []
    errors = [name for name, passed in checks.items() if not passed]
    errors.extend(replay_errors)
    return {"passed": errors == [], "checks": checks, "errors": errors}


def default_contract(claim_id: str) -> Dict[str, Any]:
    return {
        "schema": CLAIMSAFE_CONTRACT_SCHEMA,
        "claim_id": claim_id,
        "positive_claim": "This system provides bounded verification evidence for the included benchmark.",
        "claim_limit": "Only valid for the included benchmark and evidence packet.",
        "non_claims": [
            "No future performance guarantee.",
            "No live deployment readiness claim.",
            "No claim outside the included evidence packet.",
        ],
        "required_evidence": [
            "release_gate.json",
            "replay_result.json",
        ],
        "publishable_when": list(DEFAULT_PUBLISHABLE_WHEN),
        "forbidden_phrases": [
            "future return guaranteed",
            "guaranteed returns",
            "live trading ready",
        ],
        "replay_commands": [],
    }


def write_default_contract(path: Path, claim_id: str, *, overwrite: bool = False) -> Dict[str, Any]:
    if path.exists() and not overwrite:
        raise FileExistsError("refusing to overwrite existing file: " + str(path))
    payload = default_contract(claim_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload

