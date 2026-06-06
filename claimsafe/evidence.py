from __future__ import annotations

import hashlib
import json
import shutil
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

from .contract import load_contract, validate_contract

EVIDENCE_MANIFEST_NAME = "evidence_manifest.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def display_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return resolved.name


def parse_evidence_spec(spec: str) -> Tuple[Path, str]:
    if "=" in spec:
        src, dst = spec.split("=", 1)
        return Path(src), dst.replace("\\", "/")
    path = Path(spec)
    return path, path.name


def _safe_dest(output_dir: Path, rel: str) -> Path:
    if rel.startswith("/") or "\\" in rel or ".." in Path(rel).parts:
        raise ValueError("unsafe evidence destination: " + rel)
    dst = output_dir / rel
    dst.resolve().relative_to(output_dir.resolve())
    return dst


def _copy_file(src: Path, output_dir: Path, rel: str) -> None:
    if not src.is_file():
        raise FileNotFoundError("missing evidence file: " + str(src))
    dst = _safe_dest(output_dir, rel)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(str(src), str(dst))


def _file_entries(output_dir: Path) -> List[Dict[str, Any]]:
    entries: List[Dict[str, Any]] = []
    for path in sorted(output_dir.rglob("*")):
        if not path.is_file() or path.name == EVIDENCE_MANIFEST_NAME:
            continue
        rel = path.relative_to(output_dir).as_posix()
        entries.append({"path": rel, "bytes": path.stat().st_size, "sha256": sha256_file(path)})
    return entries


def _safe_clean(output_dir: Path) -> None:
    if output_dir.exists():
        shutil.rmtree(str(output_dir))


def pack_evidence(
    contract_path: Path,
    evidence_specs: Iterable[str],
    output_dir: Path,
    *,
    clean: bool = False,
) -> Dict[str, Any]:
    contract_path = contract_path.resolve()
    output_dir = output_dir.resolve()
    if clean:
        _safe_clean(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    contract = load_contract(contract_path)
    contract_validation = validate_contract(contract)
    _copy_file(contract_path, output_dir, "claim_contract.json")

    copied: List[str] = ["claim_contract.json"]
    seen = set(copied)
    for spec in evidence_specs:
        src, rel = parse_evidence_spec(spec)
        src = src.resolve()
        if rel in seen:
            raise ValueError("duplicate evidence destination: " + rel)
        _copy_file(src, output_dir, rel)
        copied.append(rel)
        seen.add(rel)

    files = _file_entries(output_dir)
    file_paths = {entry["path"] for entry in files}
    required = list(contract.get("required_evidence", []))
    missing = [rel for rel in required if rel not in file_paths]
    checks = {
        "contract_schema_valid": contract_validation.get("passed") is True,
        "required_evidence_present": missing == [],
        "claim_contract_copied": "claim_contract.json" in file_paths,
    }
    manifest = {
        "schema": "claimsafe_evidence_manifest_v0_1",
        "status": "passed" if all(checks.values()) else "failed",
        "generated_at_unix": int(time.time()),
        "claim": {
            "claim_id": contract.get("claim_id"),
            "claim_limit": contract.get("claim_limit"),
            "non_claims": contract.get("non_claims", []),
        },
        "source_contract": display_path(contract_path),
        "output_dir": display_path(output_dir),
        "checks": checks,
        "missing_required_evidence": missing,
        "file_count": len(files),
        "files": files,
    }
    write_json(output_dir / EVIDENCE_MANIFEST_NAME, manifest)
    return manifest
