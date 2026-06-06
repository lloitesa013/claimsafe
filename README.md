# ClaimSafe

[![ClaimSafe v0.1 CI](https://github.com/lloitesa013/claimsafe/actions/workflows/claimsafe-v0.1.yml/badge.svg)](https://github.com/lloitesa013/claimsafe/actions/workflows/claimsafe-v0.1.yml)

ClaimSafe is a lightweight release gate for AI claims: define bounded claims, preserve non-claims, package evidence, verify hashes, and replay results before publication.

ClaimSafe does not prove that an AI system is correct in the world. It checks whether a published claim is scoped, evidence-backed, reproducible, and not overstated.

## Why

AI demos and benchmark posts are easy to overstate. ClaimSafe separates:

- `claim_contract.json`: what is being claimed
- `non_claims`: what is explicitly not being claimed
- `evidence_manifest.json`: which files support the claim
- `release_gate.json`: whether the scoped gate passed
- `replay_result.json`: whether the evidence can be reproduced
- SHA-256 hashes: whether evidence was changed after packaging

## Quick Demo

Run the pass/fail demo:

```bash
python ops/run_claimsafe_demo.py --clean --pretty
```

Expected result:

- clean packet passes with `publishable: true`
- `guaranteed returns` fails as an overclaim
- modified evidence fails with a hash mismatch
- failed replay evidence makes the packet non-publishable

Build and verify the Stock Harness reference packet:

```bash
python ops/build_claimsafe_stock_example.py --sample --clean --pretty
python ops/claimsafe.py --pretty verify --packet-dir dist/claimsafe_stock_harness_packet
```

The Stock Harness example shows how a financial AI research claim can be packaged as bounded, reproducible evidence without claiming future returns or live-trading readiness. The public v0.1 repo uses bundled sanitized sample artifacts; projects with real Stock Harness artifacts can omit `--sample`.

## Non-Claims

ClaimSafe does not claim model accuracy, future returns, trading performance, live deployment readiness, legal approval, medical safety, financial suitability, or universal benchmark dominance.

## License

MIT. See `LICENSE`.
