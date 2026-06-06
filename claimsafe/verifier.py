from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional

from .contract import load_contract, validate_contract
from .evidence import EVIDENCE_MANIFEST_NAME, display_path, sha256_file


def _load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError("expected JSON object: " + str(path))
    return payload


def _manifest_file_map(manifest: Mapping[str, Any]) -> Dict[str, Mapping[str, Any]]:
    files = manifest.get("files", [])
    if not isinstance(files, list):
        return {}
    return {
        str(entry.get("path")): entry
        for entry in files
        if isinstance(entry, dict) and isinstance(entry.get("path"), str)
    }


def _safe_packet_path(packet_dir: Path, rel: str) -> Optional[Path]:
    if rel.startswith("/") or "\\" in rel or ".." in Path(rel).parts:
        return None
    path = packet_dir / rel
    try:
        path.resolve().relative_to(packet_dir.resolve())
    except ValueError:
        return None
    return path


def _hash_check(packet_dir: Path, manifest: Mapping[str, Any]) -> Dict[str, Any]:
    errors: List[Dict[str, Any]] = []
    for rel, entry in sorted(_manifest_file_map(manifest).items()):
        path = _safe_packet_path(packet_dir, rel)
        if path is None:
            errors.append({"path": rel, "error": "unsafe_path"})
            continue
        if not path.is_file():
            errors.append({"path": rel, "error": "missing_file"})
            continue
        actual_bytes = path.stat().st_size
        if actual_bytes != entry.get("bytes"):
            errors.append({"path": rel, "error": "bytes_mismatch", "expected": entry.get("bytes"), "actual": actual_bytes})
        actual_sha = sha256_file(path)
        if actual_sha != entry.get("sha256"):
            errors.append({"path": rel, "error": "sha256_mismatch", "expected": entry.get("sha256"), "actual": actual_sha})
    return {"passed": errors == [], "errors": errors}


def _required_evidence_check(contract: Mapping[str, Any], manifest: Mapping[str, Any]) -> Dict[str, Any]:
    file_map = _manifest_file_map(manifest)
    required = list(contract.get("required_evidence", []))
    missing = [rel for rel in required if rel not in file_map]
    return {"passed": missing == [], "required": required, "missing": missing}


def _json_gate_passed(payload: Mapping[str, Any]) -> bool:
    if payload.get("status") == "failed" or payload.get("overall_status") == "failed":
        return False
    return bool(
        payload.get("status") == "passed"
        or payload.get("overall_status") == "passed"
        or payload.get("official_claim_publishable") is True
        or payload.get("official_claim_ready") is True
    )


def _release_gate_check(packet_dir: Path, contract: Mapping[str, Any]) -> Dict[str, Any]:
    required = set(contract.get("required_evidence", []))
    if "release_gate.json" not in required and not (packet_dir / "release_gate.json").exists():
        return {"passed": True, "required": False}
    path = packet_dir / "release_gate.json"
    if not path.is_file():
        return {"passed": False, "required": True, "error": "missing release_gate.json"}
    try:
        payload = _load_json(path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return {"passed": False, "required": True, "error": str(exc)}
    return {"passed": _json_gate_passed(payload), "required": True}


def _replay_check(packet_dir: Path, contract: Mapping[str, Any]) -> Dict[str, Any]:
    required = set(contract.get("required_evidence", []))
    if "replay_result.json" not in required and not (packet_dir / "replay_result.json").exists():
        return {"passed": True, "required": False}
    path = packet_dir / "replay_result.json"
    if not path.is_file():
        return {"passed": False, "required": True, "error": "missing replay_result.json"}
    try:
        payload = _load_json(path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return {"passed": False, "required": True, "error": str(exc)}
    return {"passed": _json_gate_passed(payload), "required": True}


def _lower_phrases(contract: Mapping[str, Any]) -> List[str]:
    return [phrase.lower() for phrase in contract.get("forbidden_phrases", []) if isinstance(phrase, str)]


def _forbidden_phrase_check(packet_dir: Path, contract: Mapping[str, Any]) -> Dict[str, Any]:
    phrases = _lower_phrases(contract)
    hits: List[Dict[str, Any]] = []
    claim_text = "\n".join(
        [
            str(contract.get("positive_claim", "")),
            str(contract.get("claim_limit", "")),
            str(contract.get("public_claim_text", "")),
        ]
    ).lower()
    for phrase in phrases:
        if phrase in claim_text:
            hits.append({"path": "claim_contract.json", "phrase": phrase})

    for path in sorted(packet_dir.rglob("*")):
        if not path.is_file() or path.name in ("claim_contract.json", EVIDENCE_MANIFEST_NAME):
            continue
        if path.stat().st_size > 1024 * 1024:
            continue
        try:
            text = path.read_text(encoding="utf-8").lower()
        except UnicodeDecodeError:
            continue
        rel = path.relative_to(packet_dir).as_posix()
        for phrase in phrases:
            if phrase in text:
                hits.append({"path": rel, "phrase": phrase})
    return {"passed": hits == [], "hits": hits}


def _non_claims_check(contract: Mapping[str, Any], manifest: Mapping[str, Any]) -> Dict[str, Any]:
    expected = list(contract.get("non_claims", []))
    actual = list(manifest.get("claim", {}).get("non_claims", []))
    missing = [item for item in expected if item not in actual]
    return {"passed": expected != [] and missing == [], "missing": missing}


def verify_packet(packet_dir: Path) -> Dict[str, Any]:
    packet_dir = packet_dir.resolve()
    manifest_path = packet_dir / EVIDENCE_MANIFEST_NAME
    contract_path = packet_dir / "claim_contract.json"
    manifest = _load_json(manifest_path) if manifest_path.exists() else {}
    contract = load_contract(contract_path) if contract_path.exists() else {}
    contract_validation = validate_contract(contract)
    manifest_check = {
        "passed": bool(
            manifest
            and manifest.get("schema") == "claimsafe_evidence_manifest_v0_1"
            and manifest.get("claim", {}).get("claim_id") == contract.get("claim_id")
        ),
        "manifest_path": display_path(manifest_path),
    }
    checks = {
        "contract": contract_validation,
        "manifest": manifest_check,
        "required_evidence": _required_evidence_check(contract, manifest),
        "hashes": _hash_check(packet_dir, manifest),
        "release_gate": _release_gate_check(packet_dir, contract),
        "replay": _replay_check(packet_dir, contract),
        "non_claims": _non_claims_check(contract, manifest),
        "forbidden_phrases": _forbidden_phrase_check(packet_dir, contract),
    }
    publishable = all(check.get("passed") is True for check in checks.values())
    return {
        "schema": "claimsafe_verification_result_v0_1",
        "status": "passed" if publishable else "failed",
        "publishable": publishable,
        "packet_dir": display_path(packet_dir),
        "claim_id": contract.get("claim_id"),
        "checks": checks,
    }
