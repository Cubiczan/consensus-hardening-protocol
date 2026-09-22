# Consensus Hardening Protocol

[![PyPI](https://img.shields.io/pypi/v/consensus-hardening-protocol)](https://pypi.org/project/consensus-hardening-protocol/)
[![npm](https://img.shields.io/npm/v/@cubiczan/chp)](https://www.npmjs.com/package/@cubiczan/chp)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Adversarial decision hardening for multi-agent systems. An R0 entry gate, a
mandatory adversary pass, domain-dependent score floors, a human lock, and a
signed decision record — so a high-stakes decision made by agents can be
audited after the fact.

**Canonical repo:** [icohangar-ops/consensus-hardening-protocol](https://github.com/icohangar-ops/consensus-hardening-protocol)

## Install

### Python (PyPI)

Profile A — deliberation engine, R0/foundation/adversary/human lock, CLI, and
the normative spec + conformance harness.

```bash
pip install consensus-hardening-protocol
```

- Package: [consensus-hardening-protocol](https://pypi.org/project/consensus-hardening-protocol/)
- Requires Python 3.10+ · no required dependencies

```python
from chp import CHPOrchestrator, DecisionRegistry
```

```bash
chp init --apply
```

### TypeScript (npm)

Profile B — capital / spend gate, float-aware canonical JSON, and signed audit
ledger. Lives in a sibling package so Node apps can depend on a small surface:

```bash
npm install @cubiczan/chp
```

- Package: [@cubiczan/chp](https://www.npmjs.com/package/@cubiczan/chp)
- Source: [icohangar-ops/cubiczan-chp](https://github.com/icohangar-ops/cubiczan-chp)

```ts
import { evaluateGate, approveHuman } from "@cubiczan/chp";
```

Both packages are checked against `spec/CHP-v1.0.md` golden vectors
(Python reference: 70/70 · TypeScript Profile B: 30/30).

### MCP servers (installable wedge)

| Server | Install | Role |
|--------|---------|------|
| [`@cubiczan/chp-mcp`](https://www.npmjs.com/package/@cubiczan/chp-mcp) | `npx -y @cubiczan/chp-mcp` | Profile B spend/HITL (`evaluate_spend_gate`) |
| [`@cubiczan/agent-conductor`](https://www.npmjs.com/package/@cubiczan/agent-conductor) | `npx -y @cubiczan/agent-conductor` | AGENTS.md + skills + Profile A `decision_gate` / `decision_adversary` |
| [`@cubiczan/governed-mcp-gateway`](https://www.npmjs.com/package/@cubiczan/governed-mcp-gateway) | `npx -y @cubiczan/governed-mcp-gateway` | HTTP MCP control plane (principal + vault) |
| [`@cubiczan/codesentinel-mcp`](https://www.npmjs.com/package/@cubiczan/codesentinel-mcp) | `npx -y @cubiczan/codesentinel-mcp` | Codebase health analysis |

Both are registered under the [official MCP Registry](https://registry.modelcontextprotocol.io) (`io.github.icohangar-ops/*`).

**Conformance:** Profile A **70/70** · Profile B **30/30** (golden vectors in `spec/`).

## How the pieces fit

CHP is the **engine**. MCP servers are the **transport**. Clients never call
the package directly unless they are libraries themselves.

```text
MCP client (Cursor / Claude / …)
        │  tools/call
        ▼
┌───────────────────────────┐
│  MCP server (transport)   │  ← agent-conductor, codesentinel-mcp, …
│  decision_gate            │
│  decision_adversary       │
│  evaluate_spend_gate      │
└─────────────┬─────────────┘
              │ depends on
              ▼
┌───────────────────────────┐
│  Published CHP packages   │
│  PyPI: consensus-hardening-protocol  (Profile A)
│  npm:  @cubiczan/chp                 (Profile B)
└───────────────────────────┘
```

| Layer | Role | Example |
|-------|------|---------|
| MCP client | Issues `tools/call` | Cursor, Claude Code, Copilot |
| MCP server | Exposes CHP as tools | [agent-conductor](https://github.com/icohangar-ops/agent-conductor) (`decision_gate` → R0, `decision_adversary` → triangulation) |
| Published package | Protocol implementation | this repo (PyPI) · [@cubiczan/chp](https://github.com/icohangar-ops/cubiczan-chp) (npm) |

## What it does

An agent that is confident and wrong is more dangerous than one that is slow.
CHP puts four things in the way of a decision before it is allowed to stand:

| Stage | Rule |
|---|---|
| **R0 gate** | The session cannot open unless the problem is solvable, scoped, valid and worth doing. All four, or `HALT`. |
| **Foundation** | An adversary attacks the stated assumptions and scores the foundation. The score is gated against a floor that depends on the domain — 70 general, 85 blockchain, **100 finance**. |
| **Adversary pass** | A dedicated agent argues against the emerging decision. Its findings are recorded, not summarised away. |
| **Human lock** | A provisional lock becomes a real one only when a third party confirms it. |

Every step lands in a `DecisionCase` that serialises to a signed record, so the
question "why did we do this?" has a mechanical answer.

## Quick start

```python
from chp import CHPOrchestrator, DecisionRegistry, DecisionCase, Dossier
from chp.models import FoundationAttack, FoundationDisclosure

orch = CHPOrchestrator(registry=DecisionRegistry())

case = DecisionCase(
    decision_id="fund-tier-1",
    title="Fund the enterprise tier",
    domain="capital_allocation",   # floors at 100, not 70
    created_at="2026-08-21T10:00:00Z",
    owner="cfo",
    high_stakes=True,
    dossier=Dossier(
        core_problem="Should we fund the tier?",
        goal_state=["grow ARR"],
        current_state=["18 months runway"],
        constraints=["no new raise"],
        scope=["this fiscal year"],
    ),
)

report = orch.run_initial_session(
    case=case,
    foundation_disclosure=FoundationDisclosure(
        weakest_assumptions=["Market growth continues"],
        invalidation_conditions=["Recession"],
        key_vulnerability="Revenue concentration",
    ),
    foundation_attack=FoundationAttack(
        assumption_attacks=["Market may contract"],
        vulnerability_strike="Single customer dependency",
        foundation_score=85,
    ),
)

report.foundation_verdict   # Verdict.REFRAME — 85 is below the floor of 100
report.initial_packet       # "" — nothing is emitted on a REFRAME
```

An 85 would have passed under a 70 floor. In a capital-allocation domain it does
not, and that difference is the point of the library.

## Seed a repository

```bash
chp init                 # dry run — shows what it would write
chp init --apply         # writes .chp/
```

That drops the governance kit into `.chp/` — `R0_CONFIG.yaml`, the adversarial
prompt set, the state machine, and the compliance checklist. It never replaces an
existing file unless you pass `--force`, and it is safe to re-run.

## The specification

`spec/CHP-v1.0.md` is the normative specification. It is implementation-agnostic:
any port in any language can be checked against the golden vectors.

```bash
python spec/conformance/run_conformance.py --adapter reference
# CHP v1.0 conformance — adapter: reference
#   passed  70/70
#   result  CONFORMANT
```

Ports in other languages implement a line-JSON adapter (§7.2) and run against the
same vectors:

```bash
python spec/conformance/run_conformance.py --adapter-cmd "node my-port.js"
```

Exit status is 0 only when every selected vector passes, so this drops into CI.

## Known divergences

`spec/DIVERGENCES.md` records what a survey of six shipped implementations found,
each item cited to a file and symbol, each with a conformance vector so it fails
CI rather than sitting in a comment.

The highest-severity finding, **D-A1**, was that the canonical port hardcoded a
foundation floor of 70 for every domain, so a finance decision scoring 70 cleared
a gate documented as requiring 100. That is fixed here: `chp.foundation`
resolves the floor from the domain, matches
`spec/conformance/chp_reference.py` exactly, and a test asserts the two cannot
drift apart. A domain that merely resembles a listed one — `finance_adversary`
against `finance` — still takes the default floor per spec §5.3, but logs a
warning, because reintroducing D-A1 through naming alone is too easy.

## Optional extras

```bash
pip install "consensus-hardening-protocol[resilience]"   # pulls cubiczan-resilience from PyPI
pip install "consensus-hardening-protocol[cockroachdb]"  # distributed registry
```

The `resilience` extra depends on [`cubiczan-resilience`](https://pypi.org/project/cubiczan-resilience/) (timeout, jittered backoff, circuit breaker). TypeScript / Rust ports: [`@cubiczan/resilience`](https://www.npmjs.com/package/@cubiczan/resilience) and [`resilient-call`](https://crates.io/crates/resilient-call).

Without the `resilience` extra, the package uses a dependency-free retry with
exponential backoff that honours `max_attempts` but not `timeout` — bounding an
arbitrary call without threads is not portable.

`DecisionRegistry` is in-memory by default and auto-detects a CockroachDB backend
when one is reachable. The database layer ships with the Cognitive Mesh host
rather than this package.

`chp.AdversaryMeshAgent` is an adapter for that same host. It is exported lazily,
so the package imports fine without it.

## Standard kit — evidence matrix

The portfolio **standard kit** is canonically housed in this repository
(relocated from the archived
[`_cubiczan-shared`](https://github.com/icohangar-ops/_cubiczan-shared)):
[`inject_stack.py`](inject_stack.py) seeds sibling repos with the governance +
resilience scaffolding, and [`tools/verify_evidence_matrix.py`](tools/verify_evidence_matrix.py)
is the canonical, version-stamped evidence-matrix verifier.

`inject_stack.py --kit evidence` seeds a sibling repo with the **evidence-matrix
gate**: a byte-identical, version-stamped vendored copy of the canonical verifier, a
scaffold `evidence/matrix.yaml`, the required `evidence-matrix` CI job, and (once) the
README norm that every capability claim in the repo is backed by the matrix.

Per-repo adoption: author real matrix rows from the current tree — back each claim
with evidence that exists (a test, a script, a manifest field, a hashed artifact) or
reword the claim to what is true, visibly in the PR diff — keep the CI job required,
and state the norm in the repo README. The verifier is stdlib-only, network-free, and
refuses fail-closed: there is no invocation of it that passes an unverified repo. The
part is opt-in because the scaffold matrix is failing by design; full kit behaviour is
documented in [`CUBICZAN_STACK.md`](CUBICZAN_STACK.md).

## Licence

MIT.
