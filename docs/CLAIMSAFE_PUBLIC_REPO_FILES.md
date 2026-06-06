# ClaimSafe Public Repo File List

This is the recommended v0.1 public repository surface. Keep the release small and avoid publishing unrelated experiments.

## Include

- `README.md`: use `README_CLAIMSAFE_PUBLIC.md` as the public root README
- `LICENSE`: use `claimsafe/LICENSE`
- `.github/workflows/claimsafe-v0.1.yml`
- `claimsafe/`
- `ops/claimsafe.py`
- `ops/run_claimsafe_demo.py`
- `ops/build_claimsafe_stock_example.py`
- `ops/build_claimsafe_public_repo.py`
- `tests/test_claimsafe.py`
- `docs/CLAIMSAFE_SPEC.md`
- `docs/CLAIMSAFE_QUICKSTART.md`
- `docs/CLAIMSAFE_NON_CLAIMS.md`
- `docs/CLAIMSAFE_5_MIN_DEMO.md`
- `docs/CLAIMSAFE_V0_1_RELEASE_CHECKLIST.md`
- bundled sanitized sample artifacts under `claimsafe/examples/stock_harness/sample_artifacts/`

## Include Only If Publishing The Stock Harness Example

- the public v0.1 repo can use bundled sample artifacts with `--sample`
- full Stock Harness official/evidence artifacts are optional release artifacts only after path sanitization
- no large videos, private run directories, unrelated CARLA experiments, or patent-sensitive autonomous-driving code

## Exclude

- `external_models/`, `datasets/`, large media files, private reports, and run outputs not needed for the v0.1 demo
- raw `dist/` artifacts unless they are intentionally uploaded as release artifacts
- claims that read like stock picking, trading performance, guaranteed returns, or autonomous-driving breakthrough claims
