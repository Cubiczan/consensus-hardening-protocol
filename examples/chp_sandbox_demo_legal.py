#!/usr/bin/env python3
"""
CHP Sandbox Demo — Legal Vertical
==================================
Contract review accuracy use case.
An agent recommends executing a SaaS master services agreement.
CHP catches conflicting liability caps, missing data processing addendum,
and an auto-renewal clause that contradicts the stated termination terms.

Run:  python3 examples/chp_sandbox_demo_legal.py
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any


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


# ─── Legal Scenario ─────────────────────────────────────────────────────

def scenario_contract_review() -> dict[str, Any]:
    """
    Scenario: A contract review agent evaluates a SaaS MSA for DataVault Inc.
    CHP catches conflicting liability caps ($500K vs 1x fees), missing DPA,
    and an auto-renewal clause that contradicts the stated 30-day termination notice.
    """
    return {
        "title": "SaaS Master Services Agreement — DataVault Inc. ($240K ACV)",
        "vertical": "legal",
        "input": {
            "contract_type": "MSA + SOW",
            "vendor": "DataVault Inc.",
            "acv": 240_000,
            "term_months": 36,
            "total_contract_value": 720_000,
            "jurisdiction": "New York",
            "governing_law": "New York",
            "has_dpa": False,
            "liability_caps": [
                {"section": "8.1(a)", "cap": 500_000, "type": "general liability"},
                {"section": "8.4", "cap": "1x fees paid in prior 12 months (~$240K)", "type": "data breach"},
            ],
            "termination_notice_days": 30,
            "auto_renewal": True,
            "auto_renewal_term_months": 12,
        },
        "foundation": FoundationDisclosure(
            agent_id="contract-reviewer-v1",
            claim="DataVault Inc. MSA is standard SaaS terms with acceptable liability cap of $500K and 30-day termination notice. Recommend execution as-is.",
            sources=[
                "DataVault Inc. MSA v2.4 (received 2026-05-28)",
                "DataVault Inc. SOW #2026-03 for data migration services",
                "Vendor risk assessment questionnaire (completed 2026-04)",
                "Market benchmark: SaaS MSA liability caps average $250K-$1M for $240K ACV",
                "Existing vendor comparison: 5 peer companies' MSAs in repository",
            ],
            reasoning_chain=[
                "Step 1: Vendor MSA received, reviewed all 12 sections",
                "Step 2: Liability cap of $500K in Section 8.1(a) is within market range",
                "Step 3: 30-day termination notice is standard — no special notice period needed",
                "Step 4: Indemnification clause is reciprocal, not one-sided",
                "Step 5: Recommend execution with no redlines needed",
            ],
            confidence=0.79,
        ),
        "attack": FoundationAttack(
            agent_id="adversary-chp",
            vulnerability="The MSA has a CLASHING LIABILITY STRUCTURE: Section 8.1(a) caps general liability at $500K, but Section 8.4 caps data breach liability at only '1x fees paid in prior 12 months' (~$240K) — conflicting caps for a data migration vendor who will handle PHI/PII. There is NO Data Processing Addendum (DPA), which violates NY SHIELD Act requirements for vendors processing personal data. The auto-renewal clause (12 months) conflicts with the stated 30-day termination notice — to avoid auto-renewal, the customer must give notice 90+ days before term end, effectively making it a 90-day notice period despite stating 30 days.",
            severity=0.89,
            evidence="Section 8.4 cap: $240K (1x fees) vs market standard of $500K-$1M for data breach. No DPA despite vendor handling personal data — NY SHIELD Act Sec 899-aa requires written data security agreements with third-party vendors. Auto-renewal buried in Section 10.3: 'Either party must provide written notice of non-renewal at least 90 days prior to the end of the initial term' — contradicts stated '30-day termination notice.' The SOW includes data migration of employee records (PII).",
            recommendation="R0 ESCALATE: Material issues found: (1) Clashing liability caps create ambiguity on data breach liability. (2) Missing DPA violates NY SHIELD Act. (3) Auto-renewal notice period is 90 days, not 30 as stated. Do not execute without legal review. Escalate to chief compliance counsel.",
        ),
        "expected_verdict": R0Verdict.ESCALATE,
    }


# ─── Demo Runner ────────────────────────────────────────────────────────

def run_demo_chain(scenario: dict[str, Any]) -> DecisionPacket:
    decision_id = f"chp-legal-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
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
        "Clashing liability caps: $500K general vs ~$240K data breach (Section 8.1 vs 8.4)",
        "Missing Data Processing Addendum — violates NY SHIELD Act requirements",
        "Auto-renewal notice period is 90 days, not 30 days as stated (Section 10.3)",
        "Data migration SOW includes PII but no data security provisions found",
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
        {"step": 1, "action": "load_contract_text", "hash": "lg-a1b2c3d4", "status": "verified"},
        {"step": 2, "action": "cross_reference_clauses", "hash": "lg-e5f6g7h8", "status": "verified"},
        {"step": 3, "action": "check_regulatory_compliance", "hash": "lg-i9j0k1l2", "status": "verified"},
        {"step": 4, "action": "determine_lock_state", "hash": "lg-m3n4o5p6", "status": "verified"},
        {"step": 5, "action": "record_recommendation", "hash": "lg-q7r8s9t0", "status": "verified"},
    ]
    replay_hash = "chp-sandbox-legal::" + "::".join(s["hash"] for s in sandbox_log)

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
    print("⚖️   CHP Sandbox Demo — Legal Vertical")
    print("    Contract Review Accuracy")
    print("=" * 72)

    scenario = scenario_contract_review()
    print(f"\n{'─' * 72}")
    print(f"  SCENARIO: {scenario['title']}")
    print(f"{'─' * 72}")
    pkt = run_demo_chain(scenario)
    print()

    print(f"\n{'=' * 72}")
    print(f"  ✅ Legal demo complete")
    print(f"  🔒 Lock State: {pkt.lock_state.value}")
    print(f"  🚧 R0 Verdict: {pkt.gate_result.verdict.value}")
    print(f"  📊 Confidence: {pkt.foundation.confidence:.0%} → {pkt.gate_result.adjusted_confidence:.0%}")
    print(f"{'=' * 72}")

    out = Path(__file__).resolve().parent / "chp_sandbox_demo_legal.json"
    out.write_text(json.dumps(asdict(pkt), indent=2, default=str))
    print(f"  📄 Output: {out.name}")

    return pkt


if __name__ == "__main__":
    main()
