# ClaimSafe 5-Minute Demo Script

Title: **ClaimSafe: A Release Gate for AI Claims**

Subtitle: **Stop Shipping Unverifiable AI Claims**

## 1. Problem

AI demos are easy to overstate. A benchmark screenshot rarely tells reviewers:

- what exactly is being claimed
- what is explicitly not being claimed
- which evidence files support the claim
- whether the files changed after packaging
- whether the result can be replayed

## 2. ClaimSafe Idea

ClaimSafe turns an AI claim into a small release packet:

```text
claim_contract.json
non_claims
evidence_manifest.json
release_gate.json
replay_result.json
SHA-256 hashes
```

The goal is not to prove the world is safe. The goal is to stop publishing unbounded claims without evidence.

## 3. Clean Packet

Run:

```bash
python ops/run_claimsafe_demo.py --clean --pretty
```

Point to:

```json
"clean_pass": true
```

Explain: the claim is bounded, evidence exists, hashes match, and replay evidence passes.

## 4. Overclaim Failure

Point to:

```json
"overclaim_fails": true
```

Explain: adding a phrase like `guaranteed returns` makes the packet fail before publication.

## 5. Hash Mismatch Failure

Point to:

```json
"hash_mismatch_fails": true
```

Explain: if evidence changes after packaging, the manifest catches it.

## 6. Replay Failure

Point to:

```json
"replay_result_fails": true
```

Explain: a claim should not be publishable when the replay evidence is failed.

## 7. Stock Harness Example

Run:

```bash
python ops/build_claimsafe_stock_example.py --sample --clean --pretty
python ops/claimsafe.py --pretty verify --packet-dir dist/claimsafe_stock_harness_packet
```

Point to:

```json
"publishable": true
```

Say:

> The Stock Harness example packages a financial AI research claim as bounded evidence. It does not claim future returns, live trading readiness, or investment advice.

## 8. Close

> AI claims should ship with evidence packets, not vibes.
