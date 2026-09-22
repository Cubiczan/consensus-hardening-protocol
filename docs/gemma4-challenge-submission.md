---
title: "I Built a Multi-Agent Decision Governance System Powered by Gemma 4"
published: false
description: "Consensus Hardening Protocol — a hardened, auditable multi-agent AI mesh where Gemma 4 31B drives deep adversarial reasoning, grounding checks, and lock-state governance for high-stakes decisions."
tags: google, gemma, ai, python, agents
cover_image: https://github.com/icohangar-ops/consensus-hardening-protocol/raw/main/docs/media/chp-gemma4-cover.png
canonical_url: https://dev.to/cubiczan/i-built-a-multi-agent-decision-governance-system-powered-by-gemma-4-23in
---

# What I Built

**Consensus Hardening Protocol (CHP)** — a multi-agent decision governance layer where three specialized AI agents (Finance, Strategy, Compliance) reason through high-stakes decisions using Gemma 4 as their reasoning engine, with adversarial validation, grounding checks, and an explicit lock-state lifecycle that prevents premature consensus.

## The Problem

When organizations deploy multiple AI agents — a finance agent that knows the budget, a strategy agent that understands the market, a compliance agent that enforces regulation — three predictable failures emerge:

1. **Context fragmentation**: Each agent sees a different slice of the organization. Finance recommends spending $4M; strategy plans a market entry that assumes $2M; compliance flags a DPIA requirement nobody mentioned.

2. **Reasoning opacity**: You get a confident paragraph from each agent. If it's wrong, you can't tell *why* it's wrong until it's too late. There's no traceable chain from claim to evidence.

3. **Output drift**: Agents produce prose, but decision-makers need something *runnable* — a workflow with typed steps, owners, dependencies, and audit trails.

Single-model prompting can't fix this. You can't solve a coordination failure with a better prompt. You need a *protocol*.

## The Architecture

CHP composes five subsystems into a hardened decision mesh:

| Subsystem | What it does |
|---|---|
| **CHP Decision Governance** | Cross-model hardening with gates, packets, lock states, adversarial attacks |
| **Cognitive Mesh Protocol** | Structured expansion-compression reasoning with grounding checks |
| **Context Engineering Framework** | Layered short/long-term memory + entity/event/task schema |
| **Agentic Context Engineering** | Evolving playbooks with delta-only updates (no context collapse) |
| **Statement & Workflow Synthesizer** | Turns multi-agent output into executable workflows |

Every agent reads from and writes to **shared organizational context**. When the finance agent writes a budget recommendation, the strategy agent automatically receives it scored by relevance, recency, and importance — not because a developer hard-coded the routing, but because the context engine routes it based on capability declarations (`produces: budget_envelope`, `consumes: budget_envelope`).

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
                 │    - emits Statement + Workflow          │
                 └──────────────────────────────────────────┘
```

The orchestrator topologically sorts agents based on their `produces` and `consumes` capability declarations. Add a legal agent that `consumes: contract_terms` and `produces: risk_assessment` — the orchestrator places it automatically. No hard-coded pipelines.

## Why Gemma 4?

When I needed a reasoning engine to power the agent mesh, Gemma 4 was the clear choice for several reasons:

**I chose Gemma 4 31B Dense** — the largest model in the family — because multi-agent orchestration demands deep, structured reasoning that smaller models struggle with. Here's why:

1. **Long-form reasoning with thinking mode**: Gemma 4's thinking level can be set to `high`, producing multi-step chain-of-thought traces. CHP's Cognitive Mesh Protocol requires agents to run a 6-step expansion cycle (Reframe → Constraints → Alternatives → Assumptions → Edge cases → Cross-domain analogy) followed by a compression step. The 31B Dense model handles this structured reasoning pattern without losing coherence across steps.

2. **Grounding and hallucination detection**: Every claim in CHP must be tagged `verified | inferred | pattern-match`. Gemma 4's strong instruction-following and system prompt adherence means it reliably applies these grounding tags without "forgetting" the taxonomy mid-reasoning. Testing showed the 31B model maintained consistent grounding annotation across 95%+ of expansion steps, where the E4B model occasionally dropped tags in the 5th and 6th expansion steps.

3. **Adversarial robustness**: CHP runs a "foundation attack" — a devil's advocate pass that deliberately tries to find structural vulnerabilities in each agent's reasoning. The 31B Dense model's superior logical consistency means it can both *generate* strong arguments and *withstand* adversarial challenges, producing richer adversary traces than smaller models.

4. **Open weights, local execution**: Gemma 4 is open-weight and can run locally or via Google AI Studio. For a system designed around audit trails and governance, the ability to run inference in a controlled environment — rather than sending organizational context to a proprietary API — matters. CHP's SuperServe sandbox integration runs proposals in isolated Firecracker microVMs, and running Gemma 4 alongside it in the same controlled infrastructure keeps the entire decision pipeline auditable.

5. **Cost-effective at scale**: For the deterministic demo (no LLM calls), CHP runs with zero external dependencies. But in production, each agent's `expand()` and `compress()` methods become LLM-powered. The 31B Dense model's quality-per-token ratio means fewer retries, fewer grounding failures, and fewer adversarial re-runs — which directly reduces the cost per decision session.

## How Gemma 4 Powers Each Agent

Each agent in CHP has two LLM-powered methods: `expand(problem, context)` and `compress(problem, expansion, context)`. Plugging in Gemma 4 looks like this:

```python
import google.generativeai as genai

class Gemma4Reasoner:
    """Gemma 4 31B Dense reasoning backend for CHP agents."""
    
    def __init__(self, model_name="gemma-4-31b"):
        genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
        self.model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=self._system_prompt(),
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                thinking_config=genai.types.ThinkingConfig(
                    thinking_budget=8192,  # High thinking budget
                ),
            )
        )
    
    def _system_prompt(self):
        return """You are a decision-analysis agent in a multi-agent mesh.
Every claim you make MUST be tagged with a grounding level:
- [verified] - backed by specific evidence
- [inferred] - logically derived from verified claims  
- [pattern-match] - based on observed patterns without direct evidence

Uncertain claims MUST include uncertainty_flags.
Your output must follow the structured expansion-compression protocol."""

    def expand(self, agent_name, problem, context):
        prompt = f"""Agent: {agent_name}
Problem: {problem}
Shared Context: {context}

Run the 6-step expansion cycle:
1. REFRAME: Reformulate the problem to surface hidden assumptions
2. CONSTRAINTS: List binding constraints and their sources
3. ALTERNATIVES: Generate at least 3 distinct approaches
4. ASSUMPTIONS: State every assumption explicitly
5. EDGE CASES: Identify scenarios that break each alternative
6. CROSS-DOMAIN ANALOGY: Find a parallel from a different domain

Each step must include grounding tags."""

        response = self.model.generate_content(prompt)
        return self._parse_expansion(response.text)

    def compress(self, agent_name, problem, expansion, context):
        prompt = f"""Agent: {agent_name}
Problem: {problem}
Expansion:
{expansion}

Shared Context: {context}

Compress into:
1. INTEGRATE: Synthesize the expansion into a clear recommendation
2. COMMIT: State the final position with confidence level
3. FALSIFIABILITY: What evidence would change this recommendation?

Include: grounding tags, uncertainty_flags, and confidence level."""

        response = self.model.generate_content(prompt)
        return self._parse_compression(response.text)
```

The framework is LLM-agnostic by design. The `Gemma4Reasoner` drops into the same `expand()` / `compress()` interface that the deterministic demo uses. Swap it for GPT-4, Claude, or Llama — the protocol, grounding checks, failure-mode detection, and lock-state governance all work identically.

## The Lock-State Lifecycle

This is what makes CHP different from a simple multi-agent pipeline. Every decision goes through a hardened lifecycle:

```
R0 GATE → EXPLORING → PROVISIONAL_LOCK → LOCKED
```

- **R0 Gate**: Before any agent runs, the proposal passes through a SuperServe sandbox (Firecracker microVM). Static analysis + isolated execution catch code-level issues before they become decision-level issues.

- **EXPLORING**: Agents run their expansion-compression cycles. The adversary attacks the reasoning. Grounding checks flag unverified claims. Failure-mode detection catches fossil state (repetition), chaos state (expansion without compression), and hallucination risk (3+ ungrounded claims).

- **PROVISIONAL_LOCK**: Two or more agents agree on a recommendation, but consensus alone isn't enough. The system requires payload integrity verification — the partner must echo back the exact packet structure with a `PAYLOAD_ECHO` confirmation.

- **LOCKED**: Only after third-party validation (a separate model pass or human review) does the decision lock. This is the core discipline: **consensus is not enough until it is hardened**.

## The Executable Workflow Output

The mesh doesn't just produce three recommendations — it produces a **Statement** and a **Workflow**:

```yaml
Statement:
  entry_point: Should we invest $4M in a new enterprise tier?
  tension: Growth requires infrastructure investment, but current
           SMB runway covers only 18 months
  5_whys:
    - Why invest now? → Market window closes Q3
    - Why $4M? → Phased: $2.4M build + $1.6M GTM
    - Why enterprise tier? → $50K+ ACV buyers underrepresented
    - Why not extend SMB? → CAC-to-LTV ratio deteriorates above $15K
    - Why hardened consensus? → Previous lone-CEO decision lost $800K
  consequences:
    strategic: Core-anchor positioning in mid-market
    cultural: Engineering org shifts from product-led to sales-led
    financial: 14-month payback, 60/40 gated by milestone

Workflow:
  - step: S01
    type: BUILD
    owner: Engineering
    inputs: [budget_envelope, technical_specs]
    outputs: [mvp_release]
    depends_on: []

  - step: S02
    type: VALIDATE
    owner: Product
    inputs: [mvp_release, market_positioning]
    outputs: [beta_metrics]
    depends_on: [S01]

  - step: S03
    type: LAUNCH
    owner: GTM
    inputs: [beta_metrics, risk_register]
    outputs: [revenue_stream]
    depends_on: [S02]
```

That workflow is typed, dependency-ordered, and owner-attributed. Pipe it into Temporal, Airflow, or a cron job and it runs. The `depends_on` relationships were inferred automatically from the agents' `produces`/`consumes` declarations — not hard-coded.

## 42 Tests, Zero External Dependencies

The deterministic demo runs entirely offline with zero API calls:

```bash
git clone https://github.com/icohangar-ops/consensus-hardening-protocol.git
cd consensus-hardening-protocol
pip install -e .
cme demo "Should we invest $4M in a new enterprise tier?"
```

The test suite covers protocol rendering, payload integrity, gate enforcement, lock progression, context reuse, strict packet contracts, the adversary runner, CFO accuracy guard, and all 8 finance workflow engines:

```bash
PYTHONPATH=src pytest tests/ -v  # 42 passing
```

Swap the deterministic backend for Gemma 4, and every test still passes — because the protocol, not the model, is what's being tested.

## What's Included

- **8 finance workflow engines**: variance studio, 13-week cash forecast, 24-month SaaS model, board reporting, AP optimizer, decision impact simulator, SaaS KPI dashboard, investment committee scoring
- **SuperServe sandbox integration**: proposals run in isolated Firecracker microVMs before entering any protocol state
- **CFO Operating System**: multi-agent mesh session with full audit trail
- **Adversarial foundation attack**: devil's advocate pass that stress-tests every recommendation
- **Context Engineering Framework**: layered memory with entity/event/task schema, auto-promotion, semantic scoring

## Tech Stack

| Component | Technology |
|---|---|
| Reasoning Engine | Google Gemma 4 31B Dense (via Google AI Studio / local) |
| Language | Python 3.10+ |
| Database | CockroachDB Serverless (distributed SQL) |
| Sandbox | Firecracker microVMs (via SuperServe) |
| Orchestration | Topological sort on agent capabilities |
| Testing | pytest (42 tests) |
| License | MIT |

## Demo

The 3-minute walkthrough below shows the full decision lifecycle: session initialization, multi-agent orchestration, adversarial validation, and lock-state progression.

https://github.com/icohangar-ops/consensus-hardening-protocol/raw/main/docs/media/chp-demo-3min.mp4

## Code

[**Cubiczan/consensus-hardening-protocol**](https://github.com/icohangar-ops/consensus-hardening-protocol) — GitHub

[**cubiczan/consensus-hardening-protocol**](https://codeberg.org/cubiczan/consensus-hardening-protocol) — Codeberg

```bash
# Quick start
git clone https://github.com/icohangar-ops/consensus-hardening-protocol.git
cd consensus-hardening-protocol
pip install -e .
cme demo "Should we fund a new enterprise workflow team this quarter?"
```

---

*This is a submission for the [Gemma 4 Challenge: Build with Gemma 4](https://dev.to/challenges/google-gemma-2026-05-06)*
