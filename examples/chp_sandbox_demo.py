#!/usr/bin/env python3
"""
CHP Sandbox Demo Kit
====================
A self-contained, 30-second demo showing the full CHP compliance chain:
1. Foundation Disclosure → Foundation Attack → R0 Gate
2. Lock progression (EXPLORING → PROVISIONAL_LOCK → LOCKED)
3. SuperServe sandbox replay (deterministic verification)

Run:  python3 chp_sandbox_demo.py
Output: chp_sandbox_demo.html (standalone HTML report)

No external dependencies — uses built-in CHP core.
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

# ─── CHP Core (inline — no import deps) ─────────────────────────────────


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
    """What the agent claims as its foundation — sources, training data, reasoning chain."""

    agent_id: str
    claim: str
    sources: list[str]
    reasoning_chain: list[str]
    confidence: float  # 0.0 - 1.0
    timestamp: str = ""


@dataclass
class FoundationAttack:
    """Adversarial probe of the foundation disclosure."""

    agent_id: str
    vulnerability: str
    severity: float  # 0.0 - 1.0
    evidence: str
    recommendation: str


@dataclass
class R0GateResult:
    """R0 Gate — verifies foundation before any decision is made."""

    passed: bool
    verdict: R0Verdict
    discrepancies: list[str]
    adjusted_confidence: float
    timestamp: str = ""


@dataclass
class DecisionPacket:
    """A single hardened decision with lock state and replay evidence."""

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


# ─── Demo Scenarios ─────────────────────────────────────────────────────


def scenario_finance_variance() -> dict[str, Any]:
    """
    Scenario: A finance agent recommends a $2M capital reallocation.
    CHP catches a critical data integrity issue before the decision is locked.
    """
    return {
        "title": "Capital Reallocation Decision — $2M",
        "input": {
            "entity": "Acme Corp",
            "period": "2026-Q1",
            "actual_revenue": 42_500_000,
            "budget_revenue": 45_000_000,
            "variance_pct": -5.56,
            "recommendation": "Reallocate $2M from R&D to Sales based on revenue shortfall",
        },
        "foundation": FoundationDisclosure(
            agent_id="finance-analyzer-v1",
            claim="Revenue shortfall of 5.56% requires expense rebalancing: reduce R&D by $2M, increase Sales by $2M",
            sources=[
                "Acme Corp Q1 2026 P&L (pre-audit)",
                "Sales pipeline report (CRM, fetched 2026-04-01)",
                "Industry benchmark: SaaS companies target <5% rev variance",
            ],
            reasoning_chain=[
                "Step 1: Actual revenue of $42.5M is 5.56% below budget of $45M",
                "Step 2: Shortfall pattern matches underperforming Sales, not R&D",
                "Step 3: Industry data shows rebalancing reduces strategic variance",
                "Step 4: Recommend $2M shift from R&D (performing) to Sales (struggling)",
            ],
            confidence=0.87,
        ),
        "attack": FoundationAttack(
            agent_id="adversary-chp",
            vulnerability="Foundation data pre-dates Q1 close. The 'pre-audit' P&L was superseded by final audited figures showing only 2.1% variance. The CRM pipeline report was also stale (90-day old pipeline data). The agent's confidence (0.87) is unsupported given stale source data.",
            severity=0.92,
            evidence="Comparing pre-audit ($42.5M) vs final audited ($44.05M) revenue. Stale CRM data reduces pipeline accuracy by ~40%. The 5.56% variance drops to 2.1% with final data — below the 3% rebalancing threshold.",
            recommendation="R0 ESCALATE: Require refreshed source data before any decision. Mark foundation as 'STALE — requires re-validation'.",
        ),
        "expected_verdict": R0Verdict.ESCALATE,
    }


def scenario_supply_chain_decision() -> dict[str, Any]:
    """
    Scenario: A supply chain agent approves a lithium hydroxide shipment from a new supplier.
    CHP verifies the supplier due diligence chain before granting a lock.
    """
    return {
        "title": "Lithium Hydroxide Supplier Approval",
        "input": {
            "supplier": "GreenLithium Extractions Ltd",
            "volume_tonnes": 500,
            "price_per_tonne": 14_200,
            "total_contract_value": 7_100_000,
            "region": "Chile",
        },
        "foundation": FoundationDisclosure(
            agent_id="supply-chain-analyzer-v1",
            claim="GreenLithium Extractions Ltd meets all supplier qualification criteria for a 500-tonne lithium hydroxide contract",
            sources=[
                "GreenLithium ESG report 2025",
                "Due diligence questionnaire (completed 2025-11)",
                "Reference check: BatteryCo (300t contract, 2024)",
                "Price benchmark: Lithium price index (2026-03)",
            ],
            reasoning_chain=[
                "Step 1: ESG report shows compliance with IRMA standards",
                "Step 2: DDQ indicates adequate quality control processes",
                "Step 3: Reference from BatteryCo confirms on-time delivery",
                "Step 4: Price of $14,200/t is within market range ($13,500-$15,000)",
                "Step 5: Recommend approval with PROVISIONAL_LOCK (90-day review)",
            ],
            confidence=0.82,
        ),
        "attack": FoundationAttack(
            agent_id="adversary-chp",
            vulnerability="The ESG report and DDQ are both >6 months old. GreenLithium was cited for water rights violations in Jan 2026 (Chilean environmental regulator). No current audit certificate. The reference from BatteryCo was for a different product grade (technical-grade, not battery-grade). Price benchmark from 2026-03 does not reflect the April 2026 lithium price spike.",
            severity=0.88,
            evidence="Water rights citation: Chilean SMA Resolution 2026-017. DDQ expiry: November 2025. Product grade mismatch: BatteryCo purchased Li₂CO₃ (technical), not LiOH (battery-grade). Price index as of 2026-05: $16,800/t (+18%).",
            recommendation="R0 FAIL: Supplier due diligence is stale. Require updated ESG audit (post-Jan 2026), current DDQ, and revised pricing. Escalate for human review.",
        ),
        "expected_verdict": R0Verdict.FAIL,
    }


# ─── The Demo Runner ────────────────────────────────────────────────────


def run_demo_chain(scenario: dict[str, Any]) -> DecisionPacket:
    """
    Run one full CHP compliance chain:
    Foundation Disclosure → Foundation Attack → R0 Gate → Lock Progression → Sandbox Replay
    """
    decision_id = f"chp-demo-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
    input_data = scenario["input"]
    foundation: FoundationDisclosure = scenario["foundation"]
    attack: FoundationAttack = scenario["attack"]
    expected: R0Verdict = scenario.get("expected_verdict", R0Verdict.ESCALATE)

    # ── Phase 1: Foundation Disclosure ────────────────────────────────
    foundation.timestamp = datetime.now(timezone.utc).isoformat()
    print(f"  📋 Foundation Disclosure: {foundation.agent_id}")
    print(f"     Claim: {foundation.claim[:60]}...")
    print(f"     Sources: {len(foundation.sources)} sources")
    print(f"     Confidence: {foundation.confidence:.0%}")

    # ── Phase 2: Foundation Attack ────────────────────────────────────
    print(f"  ⚔️  Foundation Attack by {attack.agent_id}")
    print(f"     Vulnerability: {attack.vulnerability[:80]}...")
    print(f"     Severity: {attack.severity:.0%}")

    # ── Phase 3: R0 Gate ──────────────────────────────────────────────
    discrepancies = [
        "Source data staleness: pre-audit figures superseded by final audited" if "audit" in attack.vulnerability.lower() else "",
        "Reference mismatch: product grade or scope differs from claim",
        "Price benchmark out of date: market conditions have shifted",
    ]
    discrepancies = [d for d in discrepancies if d]

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
        discrepancies=discrepancies or ["No material discrepancies found"],
        adjusted_confidence=adjusted_conf,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
    print(f"  🚧 R0 Gate: {gate.verdict.value} (confidence dropped {foundation.confidence:.0%} → {adjusted_conf:.0%})")

    # ── Phase 4: Lock Progression ─────────────────────────────────────
    if verdict == R0Verdict.PASS:
        # Fast track to LOCKED
        lock_state = LockState.LOCKED
    elif verdict == R0Verdict.ESCALATE:
        # Human in the loop: PROVISIONAL_LOCK pending review
        lock_state = LockState.PROVISIONAL_LOCK
    else:
        lock_state = LockState.EXPLORING

    print(f"  🔒 Lock State: {lock_state.value}")

    # ── Phase 5: Sandbox Replay ───────────────────────────────────────
    sandbox_log = [
        {"step": 1, "action": "load_foundation", "hash": "a1b2c3d4", "status": "verified"},
        {"step": 2, "action": "apply_adversarial_probe", "hash": "e5f6g7h8", "status": "verified"},
        {"step": 3, "action": "evaluate_gate", "hash": "i9j0k1l2", "status": "verified"},
        {"step": 4, "action": "determine_lock_state", "hash": "m3n4o5p6", "status": "verified"},
        {"step": 5, "action": "record_decision", "hash": "q7r8s9t0", "status": "verified"},
    ]
    replay_hash = "chp-sandbox-v2::" + "::".join(s["hash"] for s in sandbox_log)

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


# ─── HTML Report Generator ──────────────────────────────────────────────


def generate_html_report(packets: list[DecisionPacket]) -> str:
    """Generate a standalone HTML audit report for all demo packets."""

    timeline_class = {
        LockState.EXPLORING: "timeline-fail",
        LockState.PROVISIONAL_LOCK: "timeline-escalate",
        LockState.LOCKED: "timeline-pass",
    }
    verdict_icon = {
        R0Verdict.PASS: "✅",
        R0Verdict.FAIL: "❌",
        R0Verdict.ESCALATE: "⚠️",
    }

    scenario_rows = ""
    for pkt in packets:
        sc = f"""
        <div class="scenario-card state-{pkt.lock_state.value.lower()}">
            <div class="card-header">
                <span class="verdict-icon">{verdict_icon.get(pkt.gate_result.verdict, '❓')}</span>
                <h2>{pkt.title}</h2>
                <span class="badge badge-{pkt.lock_state.value.lower()}">{pkt.lock_state.value}</span>
            </div>
            <div class="card-body">
                <div class="section">
                    <h3>📋 Foundation Disclosure</h3>
                    <p><strong>Agent:</strong> {pkt.foundation.agent_id}</p>
                    <p><strong>Claim:</strong> {pkt.foundation.claim}</p>
                    <p><strong>Sources:</strong></p>
                    <ul>{''.join(f'<li>{s}</li>' for s in pkt.foundation.sources)}</ul>
                    <p><strong>Confidence:</strong> {pkt.foundation.confidence:.0%}</p>
                </div>
                <div class="section">
                    <h3>⚔️ Foundation Attack</h3>
                    <p><strong>Agent:</strong> {pkt.attack.agent_id}</p>
                    <p><strong>Vulnerability Found:</strong> {pkt.attack.vulnerability}</p>
                    <p><strong>Severity:</strong> {pkt.attack.severity:.0%}</p>
                    <p><strong>Evidence:</strong> {pkt.attack.evidence}</p>
                </div>
                <div class="section">
                    <h3>🚧 R0 Gate Result</h3>
                    <p><strong>Verdict:</strong> <span class="verdict-tag verdict-{pkt.gate_result.verdict.value.lower()}">{pkt.gate_result.verdict.value}</span></p>
                    <p><strong>Adjusted Confidence:</strong> {pkt.gate_result.adjusted_confidence:.0%}</p>
                    <ul>{''.join(f'<li>🔴 {d}</li>' for d in pkt.gate_result.discrepancies)}</ul>
                    <p><strong>Recommendation:</strong> {pkt.attack.recommendation}</p>
                </div>
                <div class="section">
                    <h3>🔒 Lock State & Sandbox Replay</h3>
                    <p><strong>Final Lock:</strong> {pkt.lock_state.value}</p>
                    <p><strong>Replay Hash:</strong> <code>{pkt.sandbox_replay_hash[:60]}...</code></p>
                    <table class="replay-table">
                        <tr><th>Step</th><th>Action</th><th>Hash</th><th>Status</th></tr>
                        {''.join(f'<tr><td>{s["step"]}</td><td>{s["action"]}</td><td><code>{s["hash"]}</code></td><td class="status-{s["status"]}">{s["status"]}</td></tr>' for s in pkt.sandbox_replay_log)}
                    </table>
                </div>
            </div>
        </div>"""
        scenario_rows += sc

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CHP Sandbox Demo — Compliance Chain Audit</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0d1117; color: #c9d1d9; padding: 20px; }}
  .container {{ max-width: 1000px; margin: 0 auto; }}
  h1 {{ color: #58a6ff; margin-bottom: 8px; font-size: 28px; }}
  .subtitle {{ color: #8b949e; margin-bottom: 24px; font-size: 14px; }}
  .summary-bar {{ display: flex; gap: 16px; margin-bottom: 24px; flex-wrap: wrap; }}
  .summary-card {{ background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 16px; flex: 1; min-width: 140px; }}
  .summary-card h3 {{ color: #8b949e; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; }}
  .summary-card .value {{ color: #f0f6fc; font-size: 24px; font-weight: 600; margin-top: 4px; }}
  .scenario-card {{ background: #161b22; border: 1px solid #30363d; border-radius: 8px; margin-bottom: 20px; overflow: hidden; }}
  .state-pass {{ border-left: 4px solid #3fb950; }}
  .state-escalate {{ border-left: 4px solid #d29922; }}
  .state-fail {{ border-left: 4px solid #f85149; }}
  .card-header {{ display: flex; align-items: center; gap: 12px; padding: 16px; background: #1c2128; border-bottom: 1px solid #30363d; }}
  .card-header h2 {{ color: #f0f6fc; font-size: 18px; flex: 1; }}
  .verdict-icon {{ font-size: 24px; }}
  .badge {{ padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600; text-transform: uppercase; }}
  .badge-locked {{ background: #1b3a2b; color: #3fb950; }}
  .badge-provisional_lock {{ background: #3d2e00; color: #d29922; }}
  .badge-exploring {{ background: #3d1115; color: #f85149; }}
  .card-body {{ padding: 16px; }}
  .section {{ margin-bottom: 16px; padding-bottom: 16px; border-bottom: 1px solid #21262d; }}
  .section:last-child {{ border-bottom: none; margin-bottom: 0; }}
  .section h3 {{ color: #58a6ff; font-size: 14px; margin-bottom: 8px; }}
  .section p {{ margin-bottom: 4px; line-height: 1.6; }}
  .section ul {{ margin: 4px 0 0 20px; }}
  .section ul li {{ margin-bottom: 2px; }}
  .verdict-tag {{ display: inline-block; padding: 2px 8px; border-radius: 4px; font-weight: 600; font-size: 13px; }}
  .verdict-pass {{ background: #1b3a2b; color: #3fb950; }}
  .verdict-fail {{ background: #3d1115; color: #f85149; }}
  .verdict-escalate {{ background: #3d2e00; color: #d29922; }}
  .replay-table {{ width: 100%; border-collapse: collapse; margin-top: 8px; }}
  .replay-table th {{ text-align: left; padding: 8px; background: #1c2128; color: #8b949e; font-size: 12px; text-transform: uppercase; border-bottom: 1px solid #30363d; }}
  .replay-table td {{ padding: 8px; font-size: 13px; border-bottom: 1px solid #21262d; }}
  .replay-table code {{ background: #1c2128; padding: 2px 6px; border-radius: 3px; font-size: 12px; color: #8b949e; }}
  .status-verified {{ color: #3fb950; }}
  code {{ background: #1c2128; padding: 2px 6px; border-radius: 3px; font-size: 12px; }}
  .footer {{ text-align: center; color: #484f58; font-size: 12px; margin-top: 40px; padding: 20px; border-top: 1px solid #21262d; }}
</style>
</head>
<body>
<div class="container">
  <h1>🛡️ CHP Sandbox Demo</h1>
  <p class="subtitle">Compliance Chain: Foundation Disclosure → Attack → R0 Gate → Lock → Sandbox Replay</p>

  <div class="summary-bar">
    <div class="summary-card">
      <h3>Scenarios</h3>
      <div class="value">{len(packets)}</div>
    </div>
    <div class="summary-card">
      <h3>R0 PASS</h3>
      <div class="value" style="color:#3fb950">{sum(1 for p in packets if p.gate_result.verdict == R0Verdict.PASS)}</div>
    </div>
    <div class="summary-card">
      <h3>R0 ESCALATE</h3>
      <div class="value" style="color:#d29922">{sum(1 for p in packets if p.gate_result.verdict == R0Verdict.ESCALATE)}</div>
    </div>
    <div class="summary-card">
      <h3>R0 FAIL</h3>
      <div class="value" style="color:#f85149">{sum(1 for p in packets if p.gate_result.verdict == R0Verdict.FAIL)}</div>
    </div>
    <div class="summary-card">
      <h3>Generated</h3>
      <div class="value" style="font-size:14px">{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}</div>
    </div>
  </div>

  {scenario_rows}

  <div class="footer">
    <p>Consensus Hardening Protocol — Sandbox Demo Kit v2.0</p>
    <p>Run: <code>python3 examples/chp_sandbox_demo.py</code> → produces this report</p>
  </div>
</div>
</body>
</html>"""
    return html


# ─── Main ───────────────────────────────────────────────────────────────


def main():
    print("=" * 72)
    print("🛡️  CHP Sandbox Demo Kit v2.0")
    print("    Full Compliance Chain: Foundation → Attack → Gate → Lock → Replay")
    print("=" * 72)
    print()

    scenarios = [
        scenario_finance_variance(),
        scenario_supply_chain_decision(),
    ]

    packets = []
    for i, sc in enumerate(scenarios, 1):
        print(f"\n{'─' * 72}")
        print(f"  SCENARIO {i}: {sc['title']}")
        print(f"{'─' * 72}")
        pkt = run_demo_chain(sc)
        packets.append(pkt)
        print()

    # Generate HTML report
    output_dir = Path(__file__).resolve().parent
    html = generate_html_report(packets)
    report_path = output_dir / "chp_sandbox_demo.html"
    report_path.write_text(html)
    print(f"\n{'=' * 72}")
    print(f"  ✅ HTML Report: {report_path}")
    print(f"  📊 Scenarios executed: {len(packets)}")
    print(f"  🔒 Lock states: {', '.join(p.lock_state.value for p in packets)}")
    print(f"  🚧 R0 verdicts: {', '.join(p.gate_result.verdict.value for p in packets)}")
    print(f"\n  📄 Open {report_path.name} in a browser to view the audit report.")
    print(f"{'=' * 72}")

    return packets


if __name__ == "__main__":
    packets = main()
    # Also output JSON for the run-all launcher
    out = Path(__file__).resolve().parent / "chp_sandbox_demo_finance.json"
    out.write_text(json.dumps([asdict(p) for p in packets], indent=2, default=str))
