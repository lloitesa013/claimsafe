# ClaimSafe Quickstart

Run from the repository root.

Three-minute demo:

```bash
python ops/run_claimsafe_demo.py --clean --pretty
```

The demo shows:

- a clean packet passing
- an overclaim failing on forbidden claim language
- a tampered evidence file failing hash verification
- a failed replay result making the packet non-publishable

Create a contract:

```bash
python ops/claimsafe.py --pretty init --claim-id demo_claim_v0_1 --output claim_contract.json
```

Build a packet:

```bash
python ops/claimsafe.py --pretty pack --contract claim_contract.json --evidence release_gate.json --evidence replay_result.json --output-dir dist/claimsafe_packet --clean
```

Verify a packet:

```bash
python ops/claimsafe.py --pretty verify --packet-dir dist/claimsafe_packet
```

Run replay commands from a contract:

```bash
python ops/claimsafe.py --pretty replay --contract claim_contract.json --output replay_result.json
```

Build the Stock Harness reference packet:

```bash
python ops/build_claimsafe_stock_example.py --sample --clean --pretty
python ops/claimsafe.py --pretty verify --packet-dir dist/claimsafe_stock_harness_packet
```

The public v0.1 quickstart uses sanitized sample artifacts. In a full Stock Harness workspace, omit `--sample` to package real official artifacts. The bridge does not replace the Stock Harness official gate.
