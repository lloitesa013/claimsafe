# ClaimSafe v0.1 Spec

ClaimSafe is a lightweight release gate for bounded AI claims. It does not prove that a claim is true in the world. It verifies that a public claim has a clear scope, required evidence, reproducible gates, stable file hashes, and preserved non-claims.

## Contract

A packet starts with `claim_contract.json`.

Required fields:

- `schema`: must be `claimsafe_contract_v0_1`
- `claim_id`: stable claim identifier
- `positive_claim`: the bounded claim being made
- `claim_limit`: the scope boundary
- `non_claims`: claims explicitly not being made
- `required_evidence`: packet-relative evidence files that must exist
- `publishable_when`: checks that must pass before publication

Optional fields:

- `forbidden_phrases`: phrases that must not appear in public claim text or packet evidence
- `replay_commands`: deterministic command arrays used by `claimsafe replay`

## Evidence Packet

`claimsafe pack` copies the contract and evidence files into a packet directory and writes `evidence_manifest.json`.

The manifest records:

- claim id, claim limit, and non-claims
- packet-relative file paths
- byte sizes
- SHA-256 hashes
- missing required evidence

## Verification

`claimsafe verify` reports `publishable: true` only when:

- the contract shape is valid
- every required evidence file is present
- every file hash matches the manifest
- `release_gate.json`, when required, passes
- `replay_result.json`, when required, passes
- non-claims from the contract are preserved in the manifest
- forbidden phrases are absent from the bounded claim text and packet evidence

## Replay

`claimsafe replay` runs command arrays from `replay_commands` without shell evaluation. The output is a `replay_result.json` with command return codes and short stdout/stderr tails.

Do not put destructive commands in `replay_commands`. ClaimSafe v0.1 treats replay as deterministic verification, not deployment.

