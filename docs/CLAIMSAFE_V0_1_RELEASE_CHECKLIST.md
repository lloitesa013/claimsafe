# ClaimSafe v0.1 Release Checklist

## Message

- Root README starts with: `ClaimSafe is a lightweight release gate for AI claims...`
- The first screen emphasizes bounded claims, non-claims, evidence packets, replay, hash verification, and publishable gates.
- Avoid front-page wording such as AI stock picker, trading performance, guaranteed returns, or autonomous-driving breakthrough.

## Packaging

- Copy `README_CLAIMSAFE_PUBLIC.md` to `README.md` in the public repo.
- Copy `claimsafe/LICENSE` to `LICENSE` in the public repo.
- Replace `OWNER/REPO` in the GitHub Actions badge.
- Keep only the files listed in `docs/CLAIMSAFE_PUBLIC_REPO_FILES.md`.
- Confirm no local absolute paths appear in public packet artifacts.

To create a staging directory:

```bash
python ops/build_claimsafe_public_repo.py --clean --pretty
```

## Validation

Run:

```bash
python -m unittest tests/test_claimsafe.py
python ops/run_claimsafe_demo.py --clean --pretty
python ops/build_claimsafe_stock_example.py --sample --clean --pretty
python ops/claimsafe.py --pretty verify --packet-dir dist/claimsafe_stock_harness_packet
```

Expected:

- `test_claimsafe.py`: OK
- ClaimSafe demo: `status: passed`
- Stock Harness packet: `publishable: true`

## Release

- Push the public repo.
- Confirm `.github/workflows/claimsafe-v0.1.yml` passes.
- Tag `v0.1.0`.
- Attach the sanitized ClaimSafe demo packet and Stock Harness packet as release artifacts if desired.
- Use the release title: `ClaimSafe v0.1.0: A Release Gate for AI Claims`.
