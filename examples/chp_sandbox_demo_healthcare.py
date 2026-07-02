#!/usr/bin/env python3
"""
CHP Sandbox Demo — Healthcare Vertical
=======================================
Clinical trial budget compliance use case.
An agent recommends budget reallocation across a Phase 2 trial.
CHP catches expired IRB approvals and stale patient enrollment data.

Run:  python3 examples/chp_sandbox_demo_healthcare.py
"""
from __future__ import annotations

import json
import sys
import textwrap
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

# ─── CHP Core (same inline core as main demo) ─────────────────────────

class LockState(str, Enum):
    EXPLORING = "EXPLORING"
    PROVISIONAL_LOCK = "PROVISIONAL_LOCK"
    LOCKED = "LOCKED"

class R0Verdict(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    ESCALATE = "ESCALATE"

@dataclass
class FoundationDisclosure:
    agent_id: str
    claim: str
    sources: list[str]
    reasoning_chain: list[str]
    confidence: float
    timestamp: str = ""

@dataclass
class FoundationAttack:
    agent_id: str
    vulnerability: str
    severity: float
    evidence: str
    recommendation: str

@dataclass
class R0GateResult:
    passed: bool
    verdict: R0Verdict
    discrepancies: list[str]
    adjusted_confidence: float
    timestamp: str = ""

@dataclass
class DecisionPacket:
    decision_id: str
    title: str
    input_data: dict[str, Any]
    lock_state: LockState
    foundation: FoundationDisclosure
    attack: FoundationAttack | None
    gate_result: R0GateResult | None
    output_data: dict[str, Any] | None = None
    sandbox_replay_hash: str = ""
    sandbox_replay_log: list[dict[str, Any]] = field(default_factory=list)

# ─── Healthcare Scenario ────────────────────────────────────────────────

def scenario_clinical_trial_budget() -> dict[str, Any]:
    """
    Scenario: A clinical trial operations agent reallocates $1.5M across
    a Phase 2 oncology trial. CHP catches expired IRB approval and
    stale patient enrollment projections before the budget is locked.
    """
    return {
        "title": "Clinical Trial Budget Reallocation — Phase 2 Oncology ($1.5M)",
        "vertical": "healthcare",
        "input": {
            "trial_id": "ONC-P2-2024-047",
            "phase": "Phase 2",
            "indication": "Metastatic melanoma",
            "current_budget": 12_000_000,
            "reallocation_amount": 1_500_000,
            "from_area": "Patient recruitment (enrollment below target)",
            "to_area": "Biomarker sequencing (higher than anticipated volume)",
            "enrolled_patients": 87,
            "target_patients": 120,
            "projected_completion": "2026-09",
        },
        "foundation": FoundationDisclosure(
            agent_id="clinical-ops-analyzer-v1",
            claim="Reallocate $1.5M from patient recruitment to biomarker sequencing. Enrollment at 87/120 (72.5%) with 3 months remaining — recruitment budget is underspent. Sequencing costs exceed projections by 40% due to expanded biomarker panel.",
            sources=[
                "Site enrollment reports (aggregated, dated 2026-04-15)",
                "IRB approval #ONC-IRB-2024-089 (approved 2024-11, 12-month term)",
                "Sequencing vendor invoice history (2026-Q1)",
                "Sponsor budget guidelines — per-patient cost estimates",
                "ClinicalTrials.gov listing NCT-047-ONC (protocol version 3.2)",
            ],
            reasoning_chain=[
                "Step 1: Enrollment at 87/120 = 72.5%, below the 80% threshold for 3 months out",
                "Step 2: Recruitment spend is tracking 25% under budget due to slower enrollment",
                "Step 3: Sequencing costs are 40% over budget from expanded panel requirements",
                "Step 4: Reallocation of $1.5M from recruitment to sequencing balances both line items",
                "Step 5: IRB approval valid through 2025-11 — no regulatory blocker",
            ],
            confidence=0.85,
        ),
        "attack": FoundationAttack(
            agent_id="adversary-chp",
            vulnerability="IRB approval #ONC-IRB-2024-089 has a 12-month term ending November 2025. It is now June 2026 — the approval expired 7 months ago. Enrollment reports are from April 2026 and do not reflect May-June site activity. The trial protocol (v3.2) was amended in February 2026 to add a new biomarker panel — the IRB never reviewed this amendment. No evidence that sites received the protocol amendment.",
            severity=0.91,
            evidence="IRB expiry: November 2025 vs current June 2026 (7 months expired). Protocol amendment v3.2 approved by sponsor Feb 2026 but IRB approval letter shows no amendment review. Enrollment data staleness: 60+ days old. Under 21 CFR 312.66, expired IRB approval means all enrollment since Nov 2025 may be non-compliant.",
            recommendation="R0 ESCALATE: IRB approval has expired. All enrollment since November 2025 is potentially non-compliant with 21 CFR 312. Protocol amendment v3.2 was never IRB-reviewed. Escalate to clinical compliance officer immediately. Halt any budget action until regulatory status is confirmed.",
        ),
        "expected_verdict": R0Verdict.ESCALATE,
    }

# ─── Demo Runner ────────────────────────────────────────────────────────

def run_demo_chain(scenario: dict[str, Any]) -> DecisionPacket:
    decision_id = f"chp-healthcare-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
    input_data = scenario["input"]
    foundation: FoundationDisclosure = scenario["foundation"]
    attack: FoundationAttack = scenario["attack"]

    foundation.timestamp = datetime.now(timezone.utc).isoformat()
    print(f"  📋 Foundation Disclosure: {foundation.agent_id}")
    print(f"     Claim: {foundation.claim[:60]}...")
    print(f"     Sources: {len(foundation.sources)} sources")
    print(f"     Confidence: {foundation.confidence:.0%}")

    print(f"  ⚔️  Foundation Attack by {attack.agent_id}")
    print(f"     Vulnerability: {attack.vulnerability[:80]}...")
    print(f"     Severity: {attack.severity:.0%}")

    discrepancies = [
        "IRB approval expired: 12-month term ended November 2025, current date is June 2026",
        "Protocol amendment v3.2 (Feb 2026) not reviewed by IRB",
        "Enrollment data stale: 60+ days old, May-June activity not reflected",
        "Regulatory risk: enrollment under expired IRB may violate 21 CFR 312.66",
    ]

    adjusted_conf = foundation.confidence - (attack.severity * 0.5)
    adjusted_conf = max(0.05, min(adjusted_conf, 1.0))

    if attack.severity > 0.80:
        verdict = R0Verdict.ESCALATE
        passed = False
    elif attack.severity > 0.50:
        verdict = R0Verdict.FAIL
        passed = False
    else:
        verdict = R0Verdict.PASS
        passed = True

    gate = R0GateResult(
        passed=passed,
        verdict=verdict,
        discrepancies=discrepancies,
        adjusted_confidence=adjusted_conf,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
    print(f"  🚧 R0 Gate: {gate.verdict.value} (confidence dropped {foundation.confidence:.0%} → {adjusted_conf:.0%})")

    if verdict == R0Verdict.PASS:
        lock_state = LockState.LOCKED
    elif verdict == R0Verdict.ESCALATE:
        lock_state = LockState.PROVISIONAL_LOCK
    else:
        lock_state = LockState.EXPLORING
    print(f"  🔒 Lock State: {lock_state.value}")

    sandbox_log = [
        {"step": 1, "action": "load_foundation", "hash": "hc-a1b2c3d4", "status": "verified"},
        {"step": 2, "action": "apply_adversarial_probe", "hash": "hc-e5f6g7h8", "status": "verified"},
        {"step": 3, "action": "check_regulatory_compliance", "hash": "hc-i9j0k1l2", "status": "verified"},
        {"step": 4, "action": "determine_lock_state", "hash": "hc-m3n4o5p6", "status": "verified"},
        {"step": 5, "action": "record_decision", "hash": "hc-q7r8s9t0", "status": "verified"},
    ]
    replay_hash = "chp-sandbox-healthcare::" + "::".join(s["hash"] for s in sandbox_log)

    packet = DecisionPacket(
        decision_id=decision_id,
        title=scenario["title"],
        input_data=input_data,
        lock_state=lock_state,
        foundation=foundation,
        attack=attack,
        gate_result=gate,
        output_data={"final_verdict": verdict.value, "recommendation": attack.recommendation},
        sandbox_replay_hash=replay_hash,
        sandbox_replay_log=sandbox_log,
    )
    return packet


def main():
    print("=" * 72)
    print("🏥  CHP Sandbox Demo — Healthcare Vertical")
    print("    Clinical Trial Budget Compliance")
    print("=" * 72)

    scenario = scenario_clinical_trial_budget()
    print(f"\n{'─' * 72}")
    print(f"  SCENARIO: {scenario['title']}")
    print(f"{'─' * 72}")
    pkt = run_demo_chain(scenario)
    print()

    print(f"\n{'=' * 72}")
    print(f"  ✅ Healthcare demo complete")
    print(f"  🔒 Lock State: {pkt.lock_state.value}")
    print(f"  🚧 R0 Verdict: {pkt.gate_result.verdict.value}")
    print(f"  📊 Confidence: {pkt.foundation.confidence:.0%} → {pkt.gate_result.adjusted_confidence:.0%}")
    print(f"{'=' * 72}")

    # Output JSON for combined report
    out = Path(__file__).resolve().parent / "chp_sandbox_demo_healthcare.json"
    out.write_text(json.dumps(asdict(pkt), indent=2, default=str))
    print(f"  📄 Output: {out.name}")

    return pkt


if __name__ == "__main__":
    main()
