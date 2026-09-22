"""
CHP R0 Gate — SuperServe Sandbox Integration
=============================================

Integrates the Consensus Hardening Protocol's R0 gate with SuperServe
sandboxes. Before a proposal enters the EXPLORING state, the R0 gate
runs it in an isolated Firecracker microVM and checks for:

    - System access attempts
    - Network exfiltration
    - Resource abuse
    - Suspicious patterns

Usage:
    from cubiczan.superserve import CHPGate, CHPGateResult

    gate = CHPGate(strict=True)
    result = gate.evaluate_proposal(code, proposal_id="prop-001")

    if result:
        print("✅ Proposal passed R0 gate")
    else:
        print(f"❌ Blocked: {result.violations}")

CLI:
    python -m chp_superserve check "print('hello')"
    python -m chp_superserve batch proposals.json

Connects to CHP workflow:
    gate.evaluate_proposal(code) → passes → EXPLORING state
    gate.evaluate_proposal(code) → fails → REJECTED state
"""

import json
import sys
import os

# Ensure cubiczan package is available
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from cubiczan.superserve import CHPGate, CHPGateResult


def cli():
    """Command-line interface for CHP R0 Gate."""
    import argparse

    parser = argparse.ArgumentParser(description="CHP R0 Gate — Sandboxed Proposal Tester")
    sub = parser.add_subparsers(dest="command")

    # check single proposal
    check = sub.add_parser("check", help="Evaluate a single proposal")
    check.add_argument("code", help="Python proposal code string")
    check.add_argument("--id", default=None, help="Proposal ID")
    check.add_argument("--strict", action="store_true", default=True, help="Enable strict mode")
    check.add_argument("--timeout", type=int, default=60, help="Sandbox timeout (seconds)")

    # batch
    batch = sub.add_parser("batch", help="Evaluate proposals from a JSON file")
    batch.add_argument("file", help="JSON file with list of proposals: [{code, id?}]")
    batch.add_argument("--strict", action="store_true", default=True)

    args = parser.parse_args()

    if args.command == "check":
        gate = CHPGate(strict=args.strict, timeout_seconds=args.timeout)
        result = gate.evaluate_proposal(args.code, args.id)
        print(json.dumps(result.to_dict(), indent=2))

    elif args.command == "batch":
        with open(args.file) as f:
            data = json.load(f)

        proposals = [(item["code"], item.get("id")) for item in data]
        gate = CHPGate(strict=args.strict)
        results = gate.evaluate_batch(proposals)

        output = {
            "total": len(results),
            "passed": sum(1 for r in results if r.passed),
            "failed": sum(1 for r in results if not r.passed),
            "results": [r.to_dict() for r in results],
        }
        print(json.dumps(output, indent=2))

    else:
        parser.print_help()


if __name__ == "__main__":
    cli()
