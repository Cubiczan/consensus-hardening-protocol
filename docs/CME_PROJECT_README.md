# Consensus Hardening Protocol

> **Cubiczan stack** — [Profile](https://github.com/Cubiczan) · [software-factory](https://github.com/Cubiczan/software-factory) · **You are here:** `consensus-hardening-protocol`


## Demo

[![Watch the CHP demo (~30s)](docs/media/chp-thumbnail.jpg)](docs/media/chp-demo.mp4)

> _A 30-second walkthrough of CHP: title, problem, architecture, live `chp-start` / `chp-receive` / `chp-validate` terminal sessions, hardened-vs-unhardened benchmark, and closing card. A longer mirror is also available at [`docs/media/chp-demo-3min.mp4`](docs/media/chp-demo-3min.mp4)._

<!-- chp-screenshot-gallery -->
### Screenshots

**Architecture — six composed subsystems**

![Architecture](docs/media/chp-shot-architecture.jpg)

**`chp-start` — session initialization, gate checks, adversarial foundation attack**

![chp-start terminal](docs/media/chp-shot-chp-start.jpg)

**`chp-receive` — partner packet ingestion with explicit state-machine transition**

![chp-receive terminal](docs/media/chp-shot-partner-receive.jpg)

**`chp-validate` — third-party validation promotes the item to `LOCKED`**

![chp-validate terminal](docs/media/chp-shot-validate-locked.jpg)

**Benchmark — hardened vs unhardened consensus on the same decision and models**

![Benchmark chart](docs/media/chp-shot-benchmark.jpg)
<!-- /chp-screenshot-gallery -->

### Protocol lifecycle at a glance

![CHP Protocol Phases](docs/media/chp-phases.jpg)

> _Four hardened phases (Propose -> Validate -> Triangulate -> Harden) with explicit entry gates, state transitions, and audit artifacts. `LOCKED` is the only state downstream systems may consume._

Developer and enterprise infrastructure for building hardened, human-auditable multi-agent decision workflows.

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-42%20passing-brightgreen)](tests/)

---

## What this is

As organizations deploy multiple specialized AI agents (a compliance agent, a strategy agent, an engineering agent, …), they hit three predictable failures:

1. **Context fragmentation** — each agent sees a different slice of the organization
2. **Reasoning opacity** — humans get a conclusion without seeing how it was reached
3. **Output drift** — agents produce prose; humans need something runnable

Consensus Hardening Protocol composes five well-specified subsystems to solve all three:

| Subsystem | Role | Spec it implements |
|---|---|---|
| **Consensus Hardening Protocol** | Cross-model decision hardening with gates, packets, lock states, adversarial foundation attack, VCL diagnosis, and third-party validation | `cme.chp` |
| **Cognitive Mesh Protocol** | Structured expansion ↔ compression reasoning with grounding checks | `cognitive-mesh-protocol.skill` |
| **Context Engineering Framework** | Layered short/long-term memory + entity/event/task schema | `context-engineering-framework.skill` |
| **Agentic Context Engineering** | Evolving playbooks with Generator/Reflector/Curator, delta-only updates | `agentic-context-engineering.skill` |
| *Statement & workflow synthesizer* | Turns multi-agent output into a vivid problem statement + executable workflow | *(bundled)* |

Together they form a hardened decision system: every agent reads from and writes to shared context, reasons visibly, and improves its operating playbook over time.

---

## Domain-agnostic protocol

CHP is a **domain-agnostic decision-governance layer**. It works the same way whether you're managing:

- **Finance** — capital allocation, variance analysis, board reporting
- **Supply chain & critical minerals** — MineScope ore-body reconciliation, CritMin traceability
- **Security & compliance** — SEC earnings workbenches, adversarial threat simulation
- **Engineering** — architecture review gates, deployment consensus, incident post-mortems
- **Legal** — contract review, risk scoring, regulatory impact analysis
- **Product & strategy** — roadmap prioritization, market-sizing, competitive positioning
- **Research** — experimental design review, literature synthesis confidence gates
- **Any multi-agent domain** — plug in your agents, the protocol handles the rest

Every agent type follows the same R0 → EXPLORING → PROVISIONAL → LOCKED lifecycle. The state model, packet format, and adversarial attack surface are identical regardless of domain.

---

## SuperServe integration

CHP now ships with a **SuperServe sandbox integration** that runs every proposal through an isolated Firecracker microVM before it enters any protocol state:

```
Proposal → CHP R0 Gate → [Static scan + sandbox execution] → EXPLORING state / REJECTED
```

### Why SuperServe sandboxes?

SuperServe spins up lightweight Firecracker microVMs in under a second — no Docker daemon, no image pull, no volume mounts. Each sandbox is a fresh Linux VM that disappears after execution. This gives CHP:

- **True isolation** — proposals can't access the host, other sandboxes, or persistent storage
- **Deterministic audit** — every proposal runs in an identical, throwaway environment
- **Network control** — allow only what the proposal needs (e.g. `sec.gov` for SEC scraping), deny everything else
- **No env drift** — stale Python packages, dead caches, half-written configs never accumulate
- **Verifiable trace** — sandbox ID + execution output + exit code form an immutable audit record

### How you can leverage sandboxes

The SuperServe pattern is not limited to the CHP R0 gate. You can run **any agent output through sandbox validation**:

| Use Case | What runs in the sandbox | What you get back |
|---|---|---|
| **CI validation** | `git clone` + run tests | Pass/fail, test output, sandbox ID, duration |
| **R0 security gate** | Static scan + Python execution | Violations list, exit code, locked-network audit |
| **SEC EDGAR scraping** | `curl` to sec.gov with locked egress | Raw HTML, form-type breakdown, duration |
| **Multi-agent debate** | CHP-gated proposals from competing agents | Round-by-round consensus, winner, all-pass verdict |
| **Adversarial stress test** | Edge-case inputs (empty, large, special chars) | Per-case pass/fail, details for failed cases |
| **SwarmFi market resolution** | JSON-producing Python scripts | Outcome, verification flag, full audit record |
| **Output simulation (SVP)** | Pipeline: CHP → exec → 3 edge cases | 5 challenges, pass/revise consensus, audit trail |
| **Pool health monitoring** | Live sandbox query across roles | Fleet breakdown, per-role status, uptime metrics |

### Sandbox lifecycle patterns

```
# Pattern 1: Throwaway (default for proposals)
sandbox = create → install deps → lock network → run code → read output → kill

# Pattern 2: Scraper (network-locked)
sandbox = create → lock network to sec.gov → curl EDGAR → read HTML → kill

# Pattern 3: Pooled (reusable across debate rounds)
pool = SandboxPool()
pool.acquire("agent-alpha") → install deps → round 1 → round 2 → release

# Pattern 4: CI pipeline
sandbox = create → git clone → install deps → run tests → evaluate → kill
```

### Quick start

```python
from cubiczan.superserve import CHPGate, exec_python

# R0 gate — one-liner
if CHPGate().evaluate_proposal("print('hello')"):
    print("✅ proposal safe to lock")

# General-purpose sandbox — run anything
result = exec_python("print(sum(range(100)))")
print(f"exit={result.exit_code}, out={result.text}")
```

```bash
# CLI
python -m chp_superserve check "print('hello')"
python -m chp_superserve batch proposals.json
```

---

## Quick start

```bash
git clone https://github.com/icohangar-ops/consensus-hardening-protocol.git
cd consensus-hardening-protocol
pip install -e .
cme demo
```

Or without installing:

```bash
PYTHONPATH=src python3 -m cme.cli demo
```

Both produce a full Markdown orchestration report: problem classification, per-agent reasoning traces, grounding verdicts, playbook deltas, and a final executable workflow.

---

## Consensus Hardening Protocol

CHP is the decision-governance layer for **origin-agnostic, cross-model workflows**. It is designed for high-stakes decisions where a single model answer is not good enough: the system records the foundation, attacks it, packages it for a partner model, requires echoed payload integrity, and prevents final lock until third-party validation.

The current implementation covers:

- pre-session context checks with duplicate halt and related-lock auto-population
- model parity checks that halt on significant asymmetry
- **R0 gate** and foundation score gate before packet generation
- adversarial foundation disclosure and foundation attack
- Phase 0 devil's advocate capture and Round 3 implementation devil's advocate support
- VCL diagnosis in the origin packet
- `BEGIN_PAYLOAD` / `END_PAYLOAD` packet envelopes with required `PAYLOAD_ECHO`
- structured `STATE_SNAPSHOT` persistence
- Phase 1 gate enforcement before implementation rounds
- Round 5 `PROVISIONAL -> UNRESOLVED` forcing
- `PROVISIONAL_LOCK -> LOCKED` progression only after third-party validation
- strict origin 3-section contract checks
- structured partner packet primitives for item agreements, scoring tables, flip criteria, and state snapshots
- single-winner scoring validation, ASCII-only packet checks, verification checklist runner, and max-5-round enforcement
- council-spawn and convergence-closure primitives for high-stakes low-confidence sessions
- standalone `TriangulationRunner` adversary/fact-check pass
- `AdversaryMeshAgent` wrapper for plugging the adversary into mesh orchestration
- SuperServe `CHPGate` running proposals in isolated Firecracker microVMs
- `FinancialAnalysisGuard` for finance CLI workflows
- CFO accuracy policy that demotes unresolved finance outputs to `REQUIRES_HUMAN_VERIFICATION`

The core state model lives in [`src/cme/chp`](src/cme/chp). The CFO operating layer that uses it with finance, strategy, and compliance agents lives in [`src/cme/cfo_os`](src/cme/cfo_os).

Current remaining protocol work:

- raw text parser for converting partner 7-section packets into the structured packet model
- multi-model council execution beyond the current council-spawn primitive
- hosted session URL exchange and release-grade closure reporting around the current convergence-closure primitive

Quick run:

```bash
PYTHONPATH=src python3 -m cme.cli chp-start \
  --title "Fund enterprise workflow" \
  --company "Acme" \
  --problem "Should we fund a new enterprise workflow team this quarter?" \
  --amount 2500000 \
  --payback-months 14 \
  --min-runway 12 \
  --current-runway 18
```

Full demo package:

- [CHP_DEMO_VIDEO.md](CHP_DEMO_VIDEO.md)
- [docs/CHP_FINANCE_PROJECT_ROADMAP.md](docs/CHP_FINANCE_PROJECT_ROADMAP.md)
- [examples/chp_demo_video.sh](examples/chp_demo_video.sh)
- [examples/chp_demo_partner_packet.txt](examples/chp_demo_partner_packet.txt)
- [RELEASE_NOTES_CHP.md](RELEASE_NOTES_CHP.md)
- [docs/media/README.md](docs/media/README.md)

---

## Domain Workflow Suite

CHP ships with workflow suites for multiple domains. Each workflow creates a domain artifact and attaches a CHP session so the output is auditable before it becomes a decision record.

For finance workflows, the policy is mandatory: every CLI analysis runs CHP and then spawns the `TriangulationRunner` adversary pass. Because decision-grade work has a 100% verification floor, any foundation score below `100`, any open structural vulnerability, or any open blind spot blocks final lock and marks the case `REQUIRES_HUMAN_VERIFICATION`.

| Domain | Workflow | CLI command | Output artifacts |
|---|---|---|---|
| **Finance** | Monthly CFO Variance Studio | `variance-studio` | Markdown, JSON, HTML |
| **Finance** | 13-Week Cash Forecast Engine | `cash-forecast-13w` | Markdown, JSON, Excel workbook |
| **Finance** | 24-Month SaaS Operating Model | `saas-model-24m` | Markdown, JSON, Excel workbook |
| **Finance** | Board Reporting Generator | `board-reporting-generator` | Markdown, JSON, PowerPoint deck |
| **Finance** | AP Cash & Payables Optimizer | `ap-optimizer` | Markdown, JSON, Excel workbook |
| **Finance** | CFO Decision Impact Simulator | `decision-impact-simulator` | Markdown, JSON, HTML |
| **Finance** | SaaS KPI Dashboard | `saas-kpi-dashboard` | Markdown, JSON, HTML, Excel workbook |
| **Finance** | Investment Committee Scoring Tool | `investment-committee` | Markdown, JSON, Excel workbook |
| **Security** | SEC Earnings Workbench *(coming next)* | `sec-earnings-workbench` | Markdown, JSON |
| **Supply Chain** | MineScope Reconciliation *(coming next)* | `minescope-reconcile` | Markdown, JSON, GeoJSON |
| **Multi-Agent** | CFO Operating System | `cfo-os` | Session report with mesh trace, audit trail, CHP state |
| **Multi-Agent** | Output Simulation & Validation Protocol | *(via SuperServe)* | SVPResult with challenge log, audit trail |

The finance roadmap is documented in [docs/CHP_FINANCE_PROJECT_ROADMAP.md](docs/CHP_FINANCE_PROJECT_ROADMAP.md).

---

## The 90-second demo

```bash
cme demo "Should we invest $4M in a new enterprise tier next quarter, \
          or extend SMB to cover enterprise use cases?"
```

What you'll see:

1. **Finance agent** runs first (no upstream dependencies). Expansion cycle across 6 steps — reframe, constraints, alternatives, assumptions, edge cases, cross-domain analogy — then compresses to `phased spend, 60/40 gated, 14-month payback`. Playbook gains a rule.
2. **Strategy agent** reads finance's recommendation from shared context automatically. Recommends `core anchor + 15% adjacent-market experiment`, flags what would falsify it. Existing playbook bullet gets marked `helpful`.
3. **Compliance agent** reads both upstream recommendations, produces `conditional approval` with DPIA + SCC + gated review tied to the finance milestone.
4. The synthesizer produces:
   - A **Statement** with 5 Whys, consequences across strategic/cultural/financial axes, and a strategic connection
   - An **executable Workflow** of 3 typed steps with correctly inferred `depends_on` ordering (topologically sorted from the agents' `produces`/`consumes` capabilities)

Every claim in the report traces back to an agent's expansion step, which traces back to a shared-context entity.

See [`DEMO_SCRIPT.md`](DEMO_SCRIPT.md) for the full walkthrough, recommended talking points, and expected output.

---

## Architecture

![CHP Architecture](docs/media/chp-architecture.jpg)

> _Six composed subsystems. Each is independently specifiable and composable; CHP sits at the center coordinating cross-model decision hardening._

```
                        ┌──────────────────────────┐
   ┌───── shared ──────▶│   Context Engine         │◀───── shared ─────┐
   │                    │   (entities/events/tasks │                   │
   │                    │    + short/long memory)  │                   │
   │                    └──────────────────────────┘                   │
   ▼                                                                    ▼
┌────────────────────┐     ┌────────────────────┐     ┌────────────────────┐
│ Finance Agent      │     │ Strategy Agent     │     │ Compliance Agent   │
│  ├─ Playbook (ACE) │     │  ├─ Playbook (ACE) │     │  ├─ Playbook (ACE) │
│  └─ Protocol (CMP) │     │  └─ Protocol (CMP) │     │  └─ Protocol (CMP) │
└──────────┬─────────┘     └──────────┬─────────┘     └──────────┬─────────┘
           │ produces                 │ consumes+produces        │ consumes
           ▼                          ▼                          ▼
      budget_envelope        market_positioning            risk_register
      roi_model              go_to_market                  mitigations
           │                          │                          │
           └──────────────┬───────────┴──────────────┬───────────┘
                          ▼                          ▼
                 ┌──────────────────────────────────────────┐
                 │  EnterpriseOrchestrator                  │
                 │    - topologically sorts agents          │
                 │    - routes each turn through Protocol   │
                 │    - collects outputs                    │
                 │    - emits Statement + Workflow          │
                 └──────────────────────────────────────────┘
```

### Cognitive Mesh Protocol (`cme.protocol`)

Every agent turn runs through a visible breathing cycle:

- **Expansion** (up to 6 steps): Reframe → Constraints → Alternatives → Assumptions → Edge cases → Cross-domain analogy. Each step can carry explicit `uncertainty_flags`.
- **Compression** (1–2 steps): Integrate → Commit.
- **Grounding check**: every claim is tagged `verified | inferred | pattern-match` with a confidence level. A `detect_hallucination_risk` heuristic flags unsourced authority phrases ("studies show …") and bare percentages.
- **Failure-mode detection**: `FOSSIL_STATE` (repetition), `CHAOS_STATE` (expansion without compression), `HALLUCINATION_RISK` (≥3 ungrounded claims).
- **Adaptive classification**: strategic / analytical / creative / technical — auto-detected from the problem text, calibrates cycle depth.

### Context Engine (`cme.context`)

Implements the Context Engineering Framework:

- **Layered memory**: short-term with TTL + temporal weighting, auto-promotion to long-term based on importance + access frequency.
- **Fixed-schema self-baking**: `Entity { id, type, attributes }` / `Event { timestamp, actor, action, object }` / `Task { id, goal, subtasks, owner }`.
- **Context selection** by combined score (semantic relevance 50% + recency 20% + importance 20% + frequency 10%), with ≥0.85 cosine dedup.
- **Structured messages** for inter-agent sharing — each agent receives a `snapshot_for(agent_name, query)` packet containing the entities, recent events, active tasks, and top-k relevant notes.
- Thread-safe so agents can run concurrently.

No embedding model dependency — uses deterministic lexical cosine so the demo runs offline. Swap `_score_relevance` for a real embedding call in production.

### Agentic Context Engineering (`cme.playbook`)

Each agent owns a **playbook**, not a prompt:

- Bullets are `{id, section, content, helpful, harmful}`
- Six sections: `strategies_and_hard_rules`, `useful_code_snippets`, `troubleshooting_and_pitfalls`, `apis_to_use_for_specific_information`, `verification_checklist`, `domain_concepts`
- **Delta-only updates**: `ADD`, `INCREMENT`, `MERGE`, `PRUNE`. Full regeneration is impossible by design — this is how ACE prevents context collapse.
- **Reflector** analyzes each turn's trajectory + outcome + grounding issues → insights
- **Curator** transforms insights into deltas (never full rewrites)
- **Refinement pass** prunes low-utility bullets (`helpful/(helpful+harmful) < 0.4` after 3 samples) and dedupes by cosine similarity

The demo seeds each agent's playbook with 3 starter bullets per domain and extends it on every turn.

### Statement & workflow synthesizer (`cme.bridge`)

After every agent has contributed, the synthesizer produces:

1. A **Statement** with an entry point (problem / opportunity / situation), observable tension, 5 Whys derived from each agent's reframe step, consequences (strategic / cultural / financial) with a timeline, and a strategic connection to the organization's mission.
2. A **Workflow**: each agent's recommendation becomes a typed `WorkflowStep` with `inputs` / `outputs` / `depends_on`. Dependency inference is automatic — steps that consume `budget_envelope` are ordered after the step that produces it.
3. A **completeness report** for the statement against a 5-point checklist.

---

## Repository layout

```
consensus-hardening-protocol/
├── src/
│   ├── cme/                       # Core framework
│   │   ├── chp/                   # Consensus Hardening Protocol
│   │   ├── cfo_os/                # Multi-Agent CFO Operating System
│   │   ├── finance/               # Finance workflow engines and artifacts
│   │   ├── protocol.py            # Cognitive Mesh Protocol
│   │   ├── context.py             # Context Engine (memory + schema)
│   │   ├── playbook.py            # ACE playbook + Reflector + Curator
│   │   ├── bridge.py              # Statement + Workflow synthesizer
│   │   ├── agent.py               # MeshAgent base class
│   │   ├── orchestrator.py        # EnterpriseOrchestrator
│   │   └── cli.py                 # `cme` command-line tool
│   └── demo/                      # Shipped example agents
│       ├── finance_agent.py
│       ├── strategy_agent.py
│       └── compliance_agent.py
├── examples/
│   ├── basic_demo.py              # Minimal end-to-end example
│   └── *.csv / *.json             # Workflow sample inputs
├── tests/
│   ├── test_mesh.py               # Core orchestration smoke tests
│   └── test_*                     # CHP, CFO OS, workflow tests
├── DEMO_SCRIPT.md                 # Written demo script with talking points
├── chp_superserve.py             # SuperServe sandbox integration CLI
├── pyproject.toml
└── README.md
```

---

## Building your own agent

```python
from cme.agent import AgentCapability, MeshAgent
from cme.protocol import CompressionStep, ConfidenceLevel, ExpansionStep

class LegalAgent(MeshAgent):
    def __init__(self):
        super().__init__(
            name="legal",
            capability=AgentCapability(
                domain="legal",
                produces=["contract_terms"],
                consumes=["risk_register"],
            ),
        )

    def expand(self, problem, context):
        return [
            ExpansionStep(label="Reframe", content="..."),
            ExpansionStep(label="Constraints", content="..."),
            # ...up to 6 steps
        ]

    def compress(self, problem, expansion, context):
        return (
            "final recommendation...",
            [CompressionStep(label="Integrate", content="...")],
            ConfidenceLevel.MEDIUM,
            "what would change this recommendation",
            {"contract_terms": {...}},  # structured output
        )
```

Drop the agent into `EnterpriseOrchestrator(agents=[...])` — the orchestrator discovers its `produces`/`consumes` capability and places it in the execution order automatically.

### Plugging in a real LLM

The framework is LLM-agnostic. Each agent's `expand` and `compress` are plain methods — call any model inside them. The protocol handles grounding checks, failure modes, playbook updates, and rendering regardless of what produces the reasoning.

---

## Building domain-specific agents

The protocol is domain-agnostic. The same R0 gate, state model, and adversarial simulation work for any domain:

### Supply Chain Agent (MineScope)
```python
class MineScopeAgent(MeshAgent):
    def __init__(self):
        super().__init__(
            name="minescope",
            capability=AgentCapability(
                domain="critical_minerals",
                produces=["ore_body_reconciliation", "reserve_estimate"],
                consumes=["drill_data", "geochemical_assays"],
            ),
        )
    # ...expand() and compress() as above
```

### Security Agent (SEC Earnings)
```python
class SECAgent(MeshAgent):
    def __init__(self):
        super().__init__(
            name="sec-compliance",
            capability=AgentCapability(
                domain="securities",
                produces=["filing_risk_score", "disclosure_notes"],
                consumes=["draft_filing", "prior_filings"],
            ),
        )
    # ...expand() and compress() as above
```

Every domain agent automatically gets:
- CHP R0 gate on proposals
- Adversarial attack surface testing
- AUDIT trail with sandbox IDs
- Playbook evolution from usage

---

## CLI reference

```bash
cme demo [PROBLEM]             # Run the full orchestration on a problem
  --entry-point {problem,opportunity,situation}
  --title TITLE                # Workflow title
  --json                       # JSON output instead of Markdown
  --out FILE                   # Also write Markdown report to FILE

cme playbook {finance,strategy,compliance}   # Show an agent's seeded playbook
  --json

cme context                    # Dump the seeded organizational context

cme chp-start                  # Start a CHP capital allocation session
cme chp-receive                # Attach a partner packet to an existing CHP decision
cme chp-validate               # Apply third-party validation to a CHP decision
cme chp-triangulate            # Standalone adversary/fact-check pass for a claim

# Finance workflows
cme variance-studio            # Monthly actual-vs-budget variance analysis
cme cash-forecast-13w          # 13-week cash forecast
cme cash-forecast-13w-template # Excel input template for the cash forecast
cme saas-model-24m             # 24-month SaaS operating model
cme board-reporting-generator  # Board-ready reporting package and PPTX
cme ap-optimizer               # AP cash and payables optimizer
cme decision-impact-simulator  # CFO scenario simulator
cme saas-kpi-dashboard         # SaaS KPI actual-vs-budget dashboard
cme investment-committee       # Investment committee scoring tool
cme cfo-os                     # Multi-agent CFO operating session

# SuperServe sandbox integration
python -m chp_superserve check --id "prop-001" "print('hello')"
python -m chp_superserve batch proposals.json
python -m chp_superserve --help
```

---

## SuperServe sandbox integration details

The CHP R0 gate runs proposals in isolated Firecracker microVMs through the SuperServe Python SDK (`cubiczan.superserve`). 

### What SuperServe provides

| Layer | What it does | Why it matters |
|---|---|---|
| **Firecracker microVM** | Full Linux VM, boots in ~500ms | True kernel-level isolation — no container escape risk |
| **Python SDK** | `Sandbox.commands.run()`, `exec_python()`, `exec_bash()` | No SSH, no Docker commands — just function calls |
| **Network config** | `NetworkConfig(allow_out=[...], deny_out=["0.0.0.0/0"])` | Lock egress to only what the proposal needs |
| **Auto lifecycle** | Sandbox auto-destroys after timeout | No zombie VMs, no cleanup scripts needed |
| **Audit metadata** | Tag sandboxes with `{"proposal_id": "..."}` | Trace every execution back to its proposal |

### Sandbox specification

Each sandbox used by CHP:

- Uses the `cubiczan/base` template (Ubuntu + Python + curl + git pre-installed)
- Runs on a dedicated Firecracker VM with 1 vCPU, 256MB RAM, ~1GB disk
- Gets Python auto-installed if missing (APT accesses repos during install, then network locks)
- Has a default 60-second execution timeout (configurable)
- Tags every sandbox with `{"proposal_id": id, "chp": "r0_gate"}` for audit tracing
- Destroys itself after evaluation — zero cleanup burden

### How to leverage sandboxes beyond CHP

The `cubiczan.superserve` module that powers CHP also exposes every sandbox primitive directly. You can build your own validation pipelines:

**Run arbitrary Python:**
```python
from cubiczan.superserve import exec_python, exec_bash

# Execute code in a fresh VM
result = exec_python("print('hello from an isolated microVM')")
print(result.text)  # → "hello from an isolated microVM"

# Execute shell commands
result = exec_bash("curl -s https://api.example.com/health")
print(f"exit={result.exit_code}, out={result.text[:200]}")
```

**Run proposals with network lockdown:**
```python
from cubiczan.superserve import _make_sandbox, NetworkConfig

sandbox = _make_sandbox(
    name="sensitive-analysis",
    network=NetworkConfig(
        allow_out=["api.internal.corp.com:443"],
        deny_out=["0.0.0.0/0"],
    ),
)
result = sandbox.commands.run("python3 process_data.py")
sandbox.kill()
```

**Use the SandboxPool for reusable sandboxes:**
```python
from cubiczan.superserve import SandboxPool

with SandboxPool() as pool:
    pool.acquire("agent-a").commands.run("apt-get install -y my-deps")
    pool.acquire("agent-a").commands.run("python3 -c 'print("ready")'")  # Same sandbox, deps still there
```

**CI validation pipeline (clone, install, test):**
```python
from cubiczan.superserve import ci_validate_repo

report = ci_validate_repo(
    "https://github.com/org/my-project",
    test_command="pytest tests/",
)
print(f"{report.repo_name}: {'PASS' if report.passed else 'FAIL'} in {report.duration_seconds:.1f}s")
```

**Adversarial output validation (SVP):**
```python
from cubiczan.superserve import OutputSimulator, SVPProposal

sim = OutputSimulator()
result = sim.validate_proposal(SVPProposal(
    id="prop-analysis-001",
    category="code",
    content="print('analysis complete')",
))
if result.passed:
    print(f"✅ {result.proposal.id}: all {len(result.challenges)} challenges passed")
else:
    for c in result.challenges:
        if not c.passed:
            print(f"❌ {c.description}: {c.details[:100]}")
```

**Monitor sandbox health across a fleet:**
```python
from cubiczan.superserve import PoolObserver, SandboxPool

pool = SandboxPool()
obs = PoolObserver()
obs.watch_pool("production", pool)

health = obs.get_health()
print(f"{health.total_sandboxes} active sandboxes across {health.total_fleets} fleets")
```

### Full Python API (via cubiczan.superserve)

```python
from cubiczan.superserve import (
    # Core sandbox operations
    exec_python,       # Execute Python code in a throwaway VM
    exec_bash,         # Execute shell commands in a throwaway VM
    _make_sandbox,     # Create a custom sandbox with full control
    SandboxPool,       # Reusable sandbox pool by role
    
    # CHP and validation
    CHPGate,           # R0 gate: static scan + sandbox execution
    CHPGateResult,     # Proposal result with violations list
    
    # CI pipeline
    ci_validate_repo,  # Clone repo + run tests in sandbox
    ci_validate_batch, # Validate multiple repos
    
    # SwarmFi
    SwarmFiResolver,   # Verifiable prediction market resolution
    
    # SEC scraping
    SECScraperAgent,   # Parallel SEC EDGAR filing scraper
    
    # Debate & simulation
    DebateRunner,      # Multi-agent debate with CHP gate
    OutputSimulator,   # Full adversarial validation pipeline
    PoolObserver,      # Sandbox fleet health monitoring
)
```

### CLI integration

- [`chp_superserve.py`](chp_superserve.py) — standalone CLI for R0 gate testing
- Integration with `cubiczan.superserve` via `cubiczan-tools/cubiczan/superserve.py`
- SVP (Output Simulation & Validation Protocol) extends CHP with adversarial edge case simulation (3 edge cases per proposal: empty, large, special characters)

---

## Tests

```bash
pip install pytest
PYTHONPATH=src pytest tests/ -v
```

The focused suite currently has 42 passing tests covering protocol rendering, payload integrity, gate enforcement, lock progression, context reuse, strict packet contracts, the adversary runner, CFO accuracy guard, CFO OS behavior, workbook/deck exporters, and the finance workflow engines.

---

---

## Cubiczan stack

**Start here:** [software-factory](https://github.com/Cubiczan/software-factory) · [Profile](https://github.com/Cubiczan)

Cubiczan builds **auditable AI for finance and governance** — multi-agent systems where every recommendation traces to policy, reasoning, and human approval.

### Governance & orchestration

| Repo | Role |
|------|------|
| [consensus-hardening-protocol](https://github.com/Cubiczan/consensus-hardening-protocol) | CHP — adversarial review, lock states, probabilistic confidence |
| [agent-conductor](https://github.com/Cubiczan/agent-conductor) | MCP orchestration, SKILL registry, CHP decision routing |
| [compliance-as-code-agent](https://github.com/Cubiczan/compliance-as-code-agent) | YAML policy packs, scan/fix/validate, signed audit trails |
| [cleanmandate](https://github.com/Cubiczan/cleanmandate) | Verified agent payment mandates (Cleanverse A-Pass / CCP / A-Token) |

### Corporate finance

| Repo | Role |
|------|------|
| [Strata](https://github.com/Cubiczan/Strata) | CFO maturity assessment, rubric-graded deliverables, 90-day roadmap |
| [Metabocommand](https://github.com/Cubiczan/Metabocommand) | Metabolic commerce — capital reflex, approval queues, agent action log |
| [meshcfo](https://github.com/Cubiczan/meshcfo) | Auditable multi-agent CFO — forecast, investment case, board output |
| [working-capital-optimizer](https://github.com/Cubiczan/working-capital-optimizer) | AR/AP/inventory mesh — shrink cash conversion cycle |
| [cash-flow-optimizer](https://github.com/Cubiczan/cash-flow-optimizer) | 13-week forecast, Xero + Precoro + Outlook |
| [finance-cockpit](https://github.com/Cubiczan/finance-cockpit) | Jira budget, burn rate, runway dashboard |

### How they compose

```
Brief / mandate → CHP foundation + adversarial gate
       → specialist finance agents (Strata / MeshCFO / Metabocommand / WCO)
       → policy + compliance-as-code checks
       → human approval queue (CHP lock / Metabocommand / cleanmandate)
       → signed audit export
```

**Canonical org mirror:** [icohangar-ops](https://github.com/icohangar-ops) · **Codeberg:** [cubiczan](https://codeberg.org/cubiczan)

## License

MIT. See [LICENSE](LICENSE).
