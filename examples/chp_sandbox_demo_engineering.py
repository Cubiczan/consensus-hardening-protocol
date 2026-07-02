#!/usr/bin/env python3
"""
CHP Sandbox Demo — Engineering Vertical
========================================
Architecture review gates use case.
An agent approves a database migration from PostgreSQL to a new vector DB.
CHP catches missing security review, unvalidated migration plan, and
a rollback strategy that can't actually restore the data if the migration fails.

Run:  python3 examples/chp_sandbox_demo_engineering.py
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


# ─── Engineering Scenario ───────────────────────────────────────────────

def scenario_db_migration() -> dict[str, Any]:
    """
    Scenario: An engineering agent approves migrating 2TB of production data
    from PostgreSQL to VectorDB-X. CHP catches: no security review sign-off,
    no validated migration dry-run, and a rollback plan that is purely
    theoretical (the pg_dump backup hasn't been tested for restore).
    """
    return {
        "title": "Database Migration: PostgreSQL → VectorDB-X (2TB, Production)",
        "vertical": "engineering",
        "input": {
            "source": "PostgreSQL 15 (production, 2TB, ~500M rows)",
            "target": "VectorDB-X v3.2 (new cluster, 4 nodes)",
            "data_types": ["user_profiles", "product_embeddings", "search_index", "analytics_events"],
            "estimated_downtime_minutes": 45,
            "migration_tool": "pg2vectool v1.0 (custom, built in-house)",
            "rollback_plan": "pg_dump backup taken before migration, restore if migration fails",
            "security_review_status": "not scheduled",
            "dry_run_status": "not performed",
            "team_approvals": ["engineering-lead", "product-manager"],
            "missing_approvals": ["security-team", "database-architect"],
        },
        "foundation": FoundationDisclosure(
            agent_id="infra-migration-analyzer-v1",
            claim="PostgreSQL to VectorDB-X migration is safe to proceed. The 2TB dataset migrates in ~45 minutes with pg2vectool. Rollback is available via pg_dump restore. Engineering lead and product manager have approved.",
            sources=[
                "VectorDB-X documentation: migration throughput benchmarks (150MB/s)",
                "pg2vectool v1.0 test results (dev environment, 50GB subset)",
                "Engineering architecture review meeting notes (2026-05-20)",
                "Load testing report: VectorDB-X query latency vs PostgreSQL",
                "pg_dump backup manifest (nightly, compressed)",
            ],
            reasoning_chain=[
                "Step 1: VectorDB-X benchmarks show >150MB/s throughput → 2TB migrates in <4 hours",
                "Step 2: pg2vectool tested on 50GB dev subset — no data loss or corruption",
                "Step 3: Engineering lead and PM approved — team is aligned",
                "Step 4: Nightly pg_dump provides rollback capability",
                "Step 5: Recommend proceeding with migration during maintenance window",
            ],
            confidence=0.83,
        ),
        "attack": FoundationAttack(
            agent_id="adversary-chp",
            vulnerability="NO SECURITY REVIEW: The migration moves 2TB of user profiles (including PII) and product embeddings to a new database system. Security team has not reviewed VectorDB-X's encryption-at-rest, access controls, or data isolation. NO DRY-RUN: pg2vectool was tested on a 50GB dev subset, not the full 2TB. The tool is custom-built and has never migrated anything larger than 50GB. FALSE ROLLBACK: The rollback plan assumes pg_dump backup is restorable, but the backup hasn't been validated in 6 months. A 2TB pg_restore would take 8-12 hours at best — the stated 45-minute rollback is impossible. Missing database architect approval — the person most qualified to judge this migration hasn't signed off.",
            severity=0.95,
            evidence="Security review: NOT SCHEDULED — violates Change Management Policy Section 4.2 (all production data migrations require security sign-off). Dry-run status: NOT PERFORMED — violates Engineering Runbook Section 3.1 (full dataset dry-run required for any migration >100GB). pg_dump restore test: LAST VALIDATED December 2025 (6+ months stale). Actual restore time for 2TB: estimated 8-12 hours (not 45 min). Missing approval from database architect noted in architecture review notes.",
            recommendation="R0 ESCALATE: Three blocking issues: (1) No security review — do NOT migrate PII without security sign-off. (2) No production-scale dry-run — custom tool unproven at 2TB. (3) Rollback plan is fiction — 8-12 hour restore vs claimed 45 minutes. Require: security review, full dry-run with 2TB verified subset, validated restore test, and database architect approval.",
        ),
        "expected_verdict": R0Verdict.ESCALATE,
    }


# ─── Demo Runner ────────────────────────────────────────────────────────

def run_demo_chain(scenario: dict[str, Any]) -> DecisionPacket:
    decision_id = f"chp-engineering-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
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
        "Security review not scheduled — violates Change Management Policy §4.2",
        "No production-scale dry-run performed (custom tool unproven at 2TB)",
        "Rollback plan unverified: pg_dump restore not tested in 6+ months",
        "Rollback time estimate wrong: 45 min claimed vs actual 8-12 hours",
        "Missing database architect approval — critical stakeholder not consulted",
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
        {"step": 1, "action": "load_migration_plan", "hash": "en-a1b2c3d4", "status": "verified"},
        {"step": 2, "action": "validate_security_reviews", "hash": "en-e5f6g7h8", "status": "verified"},
        {"step": 3, "action": "check_rollback_viability", "hash": "en-i9j0k1l2", "status": "verified"},
        {"step": 4, "action": "determine_lock_state", "hash": "en-m3n4o5p6", "status": "verified"},
        {"step": 5, "action": "record_decision", "hash": "en-q7r8s9t0", "status": "verified"},
    ]
    replay_hash = "chp-sandbox-engineering::" + "::".join(s["hash"] for s in sandbox_log)

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
    print("🔧  CHP Sandbox Demo — Engineering Vertical")
    print("    Architecture Review & Migration Gates")
    print("=" * 72)

    scenario = scenario_db_migration()
    print(f"\n{'─' * 72}")
    print(f"  SCENARIO: {scenario['title']}")
    print(f"{'─' * 72}")
    pkt = run_demo_chain(scenario)
    print()

    print(f"\n{'=' * 72}")
    print(f"  ✅ Engineering demo complete")
    print(f"  🔒 Lock State: {pkt.lock_state.value}")
    print(f"  🚧 R0 Verdict: {pkt.gate_result.verdict.value}")
    print(f"  📊 Confidence: {pkt.foundation.confidence:.0%} → {pkt.gate_result.adjusted_confidence:.0%}")
    print(f"{'=' * 72}")

    out = Path(__file__).resolve().parent / "chp_sandbox_demo_engineering.json"
    out.write_text(json.dumps(asdict(pkt), indent=2, default=str))
    print(f"  📄 Output: {out.name}")

    return pkt


if __name__ == "__main__":
    main()
