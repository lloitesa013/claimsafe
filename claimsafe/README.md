# ClaimSafe

ClaimSafe is a lightweight release gate for AI claims: define bounded claims, preserve non-claims, package evidence, verify hashes, and replay results before publication.

It is not a tool for proving that an AI system is correct in the world. It is a tool for checking whether a published claim is scoped, evidence-backed, reproducible, and not overstated.

## Quick Demo

Run from the repository root:

```bash
python ops/run_claimsafe_demo.py --clean --pretty
```

The demo creates four packets under `dist/claimsafe_demo`:

- clean packet: passes with `publishable: true`
- overclaim packet: fails when the claim says `guaranteed returns`
- hash mismatch packet: fails after evidence is modified
- replay failure packet: fails when replay evidence is failed

Verify the Stock Harness reference packet:

```bash
python ops/build_claimsafe_stock_example.py --sample --clean --pretty
python ops/claimsafe.py --pretty verify --packet-dir dist/claimsafe_stock_harness_packet
```

## Contract Shape

ClaimSafe v0.1 uses `claim_contract.json`:

```json
{
  "schema": "claimsafe_contract_v0_1",
  "claim_id": "demo_claim_v0_1",
  "positive_claim": "This system provides bounded verification evidence for the included benchmark.",
  "claim_limit": "Only valid for the included benchmark and evidence packet.",
  "non_claims": [
    "No future performance guarantee.",
    "No live deployment readiness claim.",
    "No claim outside the included evidence packet."
  ],
  "required_evidence": [
    "release_gate.json",
    "replay_result.json"
  ],
  "publishable_when": [
    "schema_valid",
    "required_evidence_present",
    "hashes_verified",
    "release_gate_passed",
    "replay_passed",
    "non_claims_preserved",
    "forbidden_phrases_absent"
  ]
}
```

## Non-Claims

ClaimSafe does not claim model accuracy, future returns, live deployment readiness, legal approval, medical safety, financial suitability, or universal benchmark dominance.

The Stock Harness example shows how a financial AI research claim can be packaged as bounded, reproducible evidence without claiming future returns or live-trading readiness. Use `--sample` in a fresh public clone; omit it when real Stock Harness official artifacts are present.

For public-release packaging, see `docs/CLAIMSAFE_PUBLIC_REPO_FILES.md` and `docs/CLAIMSAFE_V0_1_RELEASE_CHECKLIST.md`.
