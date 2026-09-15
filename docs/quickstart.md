# Quickstart

Get a multi-agent consensus round running in about 5 minutes.

## 1. Install

```bash
git clone https://github.com/icohangar-ops/consensus-hardening-protocol.git
cd consensus-hardening-protocol
pip install -e .
```

Prefer not to install? Run everything below with `PYTHONPATH=src` in front of the command instead — no `pip install` needed.

**What this does:** pulls in `cme` (the Cognitive Mesh Engine — agents, context, playbooks, and the CHP protocol package) and registers the `cme` CLI entry point.

## 2. Run the built-in demo

```bash
cme demo
```

or, without installing:

```bash
PYTHONPATH=src python3 -m cme.cli demo
```

**What this does:** spins up three agents (finance, strategy, compliance) against a default problem, runs each one through CHP's expansion/compression reasoning cycle, and prints a full Markdown report.

**Expected output** (trimmed):

```
# Orchestration Report
**Problem:** Should we invest $4M in building a dedicated enterprise tier next quarter, or extend the existing SMB product to cover enterprise use cases?
**Agents:** finance, strategy, compliance
**Duration:** 0ms

---

## Agent Turn — finance
## Problem Classification
Strategic — mentions strategic/market/financial terms

## Reasoning Process
### Expansion Cycle (count=1)
1. **Reframe** — Restated as a capital-allocation question: ...
2. **Constraints** — Hard: annual OPEX ceiling, regulatory reserve requirements. ...
...

## Final Recommendation
Recommend phased spend (Option A) with a 4-week discovery prepended: ...
Confidence: **high**
...

### 5 Whys
1. **Why does finance see this matter?** → Reframe: ...
2. **Why does strategy see this matter?** → Reframe: ...
3. **Why does compliance see this matter?** → Reframe: ...

## Executable Steps
- **S01** [finance] Recommend phased spend (Option A) ...
    outputs: ['budget_envelope', 'roi_model']
- **S02** [strategy] Anchor in the core segment (Option I) ... (after S01)
    outputs: ['market_positioning', 'go_to_market']
- **S03** [compliance] Approve with conditions (Option α) ... (after S01, S02)
    outputs: ['risk_register', 'mitigations']
```

Each agent runs in dependency order (finance → strategy → compliance, inferred from what each `produces`/`consumes`), reads the prior agents' conclusions from shared context, and contributes a recommendation. The synthesizer then turns all three recommendations into a single Statement (the "why") and Workflow (the "what to do next").

## 3. Or wire it up yourself

The same round from Python — this is [`examples/basic_demo.py`](../examples/basic_demo.py):

```python
from cme.bridge import EntryPoint
from cme.context import ContextEngine, Entity
from cme.orchestrator import EnterpriseOrchestrator
from demo import ComplianceAgent, FinanceAgent, StrategyAgent

# 1. Seed shared context — every agent reads from and writes to this
ctx = ContextEngine()
ctx.upsert_entity(Entity(id="org", type="org", attributes={"name": "Aperture Corp"}))
ctx.upsert_entity(
    Entity(id="ndr", type="metric", attributes={"name": "Net Dollar Retention", "current": 1.08})
)

# 2. Wire up the agents that will take part in the round
orch = EnterpriseOrchestrator(
    agents=[FinanceAgent(), StrategyAgent(), ComplianceAgent()],
    context=ctx,
)

# 3. Run the consensus round
report = orch.orchestrate(
    "Should we launch a dedicated enterprise tier next quarter?",
    entry_point=EntryPoint.OPPORTUNITY,
)

print(report.render())
```

```bash
PYTHONPATH=src python3 examples/basic_demo.py
```

What each step does:

- **`ContextEngine` + `Entity`** — the shared memory every agent reads from and writes to, so later agents see earlier agents' conclusions instead of reasoning in isolation.
- **`EnterpriseOrchestrator(agents=...)`** — topologically sorts the agents by their declared `produces`/`consumes` capabilities and runs each one's turn through the protocol in the right order.
- **`orch.orchestrate(problem, entry_point=...)`** — runs the actual consensus round: each agent expands (reframe, constraints, alternatives, assumptions, edge cases, analogy), compresses to a recommendation with a confidence level, and updates its playbook.
- **`report.render()`** — produces the Markdown report shown in step 2, including a synthesized Statement and an executable Workflow with dependency-ordered steps.

## 4. Next: hardened decisions with CHP

Steps 2–3 run the Cognitive Mesh Protocol — good for everyday multi-agent reasoning. For high-stakes decisions that need gates, adversarial testing, and third-party validation before anything locks, use the Consensus Hardening Protocol directly:

```bash
PYTHONPATH=src python3 -m cme.cli chp-start \
  --title "Pilot enterprise workflow" \
  --company "Acme" \
  --problem "Should we fund a pilot enterprise workflow team this quarter?" \
  --amount 250000 \
  --payback-months 12 \
  --min-runway 12 \
  --current-runway 18
```

**What this does:** builds a decision case, runs it through the R0 gate (is the problem solvable, scoped, and valid?), discloses and attacks its own foundation assumptions, scores the result, and packages everything into a partner packet awaiting third-party validation.

**Expected output** (trimmed):

```
[saved CHP registry to .chp_registry.json]
# CHP Session
Decision: Pilot enterprise workflow
Status: REQUIRES_HUMAN_VERIFICATION

## R0 Gate
- verdict: PASS

## Foundation
- weakest_assumptions: 3
- foundation_score: 78
- verdict: PASS

## Initial Packet
BEGIN_PAYLOAD [RX] [5LWDYO]
...
END_PAYLOAD [RX] [5LWDYO]

## CFO Accuracy Guard
- Status: REQUIRES_HUMAN_VERIFICATION
- Accuracy Floor: 100
- Blocking Violations:
  - foundation score 78 is below CFO accuracy floor 100
  - PENDING third-party validation
  ...
```

A `REQUIRES_HUMAN_VERIFICATION` status here is expected, not a failure: CHP enforces a 100% verification floor for decision-grade work, so any open structural vulnerability or missing third-party validation blocks the case from reaching `LOCKED`. That's the point of the protocol — a single agent's confident-sounding answer is never enough on its own.

## Where to go next

- [README.md — Consensus Hardening Protocol](../README.md#consensus-hardening-protocol) for the full protocol spec: gates, packet format, lock states, and adversarial validation.
- [README.md — CHP Decision Lifecycle](../README.md#chp-decision-lifecycle) for the `EXPLORING → LOCKED` state machine.
- [RELEASE_NOTES_CHP.md](../RELEASE_NOTES_CHP.md) for what's implemented today and what's still in progress.
- [DEMO_SCRIPT.md](../DEMO_SCRIPT.md) for a full walkthrough with talking points.
- [examples/](../examples/) for domain-specific workflows (finance, sandboxed proposal validation, etc.).
