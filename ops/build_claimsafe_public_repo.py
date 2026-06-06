#!/usr/bin/env python3
"""Build a minimal public ClaimSafe v0.1 repository staging directory."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = Path("dist/claimsafe_public_repo")


def _display_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return resolved.name

FILE_COPIES: List[Tuple[str, str]] = [
    ("README_CLAIMSAFE_PUBLIC.md", "README.md"),
    ("claimsafe/LICENSE", "LICENSE"),
    ("CLAIMSAFE_PUBLIC_GITIGNORE", ".gitignore"),
    (".github/workflows/claimsafe-v0.1.yml", ".github/workflows/claimsafe-v0.1.yml"),
    ("ops/claimsafe.py", "ops/claimsafe.py"),
    ("ops/run_claimsafe_demo.py", "ops/run_claimsafe_demo.py"),
    ("ops/build_claimsafe_stock_example.py", "ops/build_claimsafe_stock_example.py"),
    ("ops/build_claimsafe_public_repo.py", "ops/build_claimsafe_public_repo.py"),
    ("tests/test_claimsafe.py", "tests/test_claimsafe.py"),
    ("docs/CLAIMSAFE_SPEC.md", "docs/CLAIMSAFE_SPEC.md"),
    ("docs/CLAIMSAFE_QUICKSTART.md", "docs/CLAIMSAFE_QUICKSTART.md"),
    ("docs/CLAIMSAFE_NON_CLAIMS.md", "docs/CLAIMSAFE_NON_CLAIMS.md"),
    ("docs/CLAIMSAFE_PUBLIC_REPO_FILES.md", "docs/CLAIMSAFE_PUBLIC_REPO_FILES.md"),
    ("docs/CLAIMSAFE_5_MIN_DEMO.md", "docs/CLAIMSAFE_5_MIN_DEMO.md"),
    ("docs/CLAIMSAFE_V0_1_RELEASE_CHECKLIST.md", "docs/CLAIMSAFE_V0_1_RELEASE_CHECKLIST.md"),
]

DIR_COPIES: List[Tuple[str, str]] = [
    ("claimsafe", "claimsafe"),
]


def _safe_clean(output_dir: Path) -> None:
    resolved = output_dir.resolve()
    dist_root = (ROOT / "dist").resolve()
    if not str(resolved).startswith(str(dist_root)) or resolved.name != "claimsafe_public_repo":
        raise ValueError("refusing to clean unexpected output directory: " + str(resolved))
    if resolved.exists():
        shutil.rmtree(str(resolved))


def _ignore_generated(_dir: str, names: List[str]) -> List[str]:
    return [name for name in names if name in {"__pycache__", ".pytest_cache"} or name.endswith(".pyc")]


def _copy_file(src_rel: str, dst_rel: str, output_dir: Path) -> str:
    src = ROOT / src_rel
    if not src.is_file():
        raise FileNotFoundError("missing public repo file: " + str(src))
    dst = output_dir / dst_rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(str(src), str(dst))
    return dst_rel.replace("\\", "/")


def _copy_dir(src_rel: str, dst_rel: str, output_dir: Path) -> List[str]:
    src = ROOT / src_rel
    if not src.is_dir():
        raise FileNotFoundError("missing public repo directory: " + str(src))
    dst = output_dir / dst_rel
    if dst.exists():
        shutil.rmtree(str(dst))
    shutil.copytree(str(src), str(dst), ignore=_ignore_generated)
    copied = []
    for path in sorted(dst.rglob("*")):
        if path.is_file():
            copied.append(path.relative_to(output_dir).as_posix())
    return copied


def build_public_repo(output_dir: Path = DEFAULT_OUTPUT_DIR, *, clean: bool = False) -> dict:
    output_dir = output_dir if output_dir.is_absolute() else ROOT / output_dir
    if clean:
        _safe_clean(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    copied: List[str] = []
    for src, dst in DIR_COPIES:
        copied.extend(_copy_dir(src, dst, output_dir))
    for src, dst in FILE_COPIES:
        copied.append(_copy_file(src, dst, output_dir))
    copied = sorted(set(copied))
    forbidden_dirs = ["dist", "external_models", "datasets", "reports"]
    forbidden_present = [name for name in forbidden_dirs if (output_dir / name).exists()]
    report = {
        "schema": "claimsafe_public_repo_build_v0_1",
        "status": "passed" if not forbidden_present else "failed",
        "output_dir": _display_path(output_dir),
        "file_count": len(copied),
        "files": copied,
        "checks": {
            "root_readme_present": (output_dir / "README.md").is_file(),
            "root_license_present": (output_dir / "LICENSE").is_file(),
            "dist_not_included": not (output_dir / "dist").exists(),
            "forbidden_dirs_absent": forbidden_present == [],
        },
        "forbidden_present": forbidden_present,
    }
    return report


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Build the public ClaimSafe v0.1 repository staging directory.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--clean", action="store_true")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args(list(argv) if argv is not None else None)
    report = build_public_repo(Path(args.output_dir), clean=args.clean)
    print(json.dumps(report, indent=2 if args.pretty else None, sort_keys=True))
    return 0 if report.get("status") == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
