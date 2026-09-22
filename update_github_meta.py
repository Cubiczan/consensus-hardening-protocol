#!/usr/bin/env python3
"""Set GitHub repo descriptions and topics across the portfolio.

Discoverability was the cheapest unforced error in the 2026-07 portfolio audit:
26 of 128 repos had no description at all — including the highest-reach repo in
the dependency graph — and only 12 carried topics. A repo nobody can identify
from the listing may as well not exist.

Auth comes from the `gh` CLI, which is already authenticated. No token is read,
stored, or passed on a command line — so nothing here can leak one.

    python3 update_github_meta.py                  # dry-run (default)
    python3 update_github_meta.py --apply          # fill gaps only
    python3 update_github_meta.py --apply --overwrite-descriptions
    python3 update_github_meta.py --apply --repos market-radar,geopulse

Safe by default, in three ways:

* Without --apply nothing is written.
* An existing description is left alone unless you pass --overwrite-descriptions.
  Hand-written text beats generated text; this tool fills gaps.
* Topics are additive (`gh --add-topic`), so curated topics are never dropped.

Repo names are validated against the live org listing first, so a typo is
reported rather than 404ing halfway through a sweep.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys

ORG = "icohangar-ops"

# GitHub rejects topics that aren't lowercase alphanumeric + hyphen, max 50 chars,
# and allows at most 20 per repo. Violations 422 the whole call, so we validate.
MAX_TOPICS = 20
MAX_DESCRIPTION = 350

REPOS: dict[str, dict] = {
    # ---- governance & orchestration -------------------------------------
    "Consensus-Hardening-Protocol-The-Differ": {
        "description": "Normative CHP v1.0 spec + conformance suite — adversarial decision hardening, R0 gate, domain score floors, signed lock states",
        "topics": ["ai-governance", "ai-safety", "consensus-protocol", "multi-agent",
                   "adversarial", "decision-framework", "specification", "conformance-testing"],
    },
    "consensus-hardening-protocol": {
        "description": "CHP reference implementation — adversarial review, lock-step verification, and auditable multi-agent decisions",
        "topics": ["ai-governance", "ai-safety", "consensus-protocol", "multi-agent",
                   "adversarial", "decision-framework", "mcp", "compliance"],
    },
    "agent-conductor": {
        "description": "MCP agent conductor — AGENTS.md contracts, SKILL registry, CHP decision routing",
        "topics": ["mcp", "ai-agents", "orchestration", "governance", "typescript"],
    },
    "compliance-as-code-agent": {
        "description": "YAML compliance policy packs (SOC2/GDPR) with detect → fix → validate agent pipeline and signed audit trails",
        "topics": ["compliance", "policy-as-code", "soc2", "gdpr", "ai-agents", "governance", "rust"],
    },
    "cleanmandate": {
        "description": "Verified AI agent payment mandates — Cleanverse A-Pass, CCP, A-Token on Monad (Rust)",
        "topics": ["rust", "ai-agents", "compliance", "stablecoin", "monad", "travel-rule", "governance"],
    },
    "complyai": {
        "description": "AI compliance review for fintech marketing — flags SEC/FCA regulatory red flags in landing pages and comms before publication",
        "topics": ["compliance", "fintech", "regtech", "marketing", "ai-agents", "sec", "fca"],
    },
    "shieldgate": {
        "description": "Least-privilege agentic SOC — SpiceDB ReBAC authorization for AI security operations over Splunk (AuthZed × Splunk)",
        "topics": ["security", "authorization", "spicedb", "rebac", "splunk", "soc", "ai-agents", "zero-trust"],
    },
    "cubiczan-resilience": {
        "description": "Shared resilience primitives — safeFetch/@resilient, signed HMAC audit ledger, three-tier live→cache→mock fallback (TS/Python/Rust)",
        "topics": ["resilience", "circuit-breaker", "retry", "audit-log", "typescript", "python", "rust", "observability"],
    },
    "cubiczan-eval": {
        "description": "LLM-as-a-Judge + self-improvement harness — rubric scoring, rolling averages, grade-revise loop for Python agent systems",
        "topics": ["llm-evaluation", "llm-as-judge", "ai-agents", "python", "testing", "self-improvement"],
    },

    # ---- corporate finance ----------------------------------------------
    "strata": {
        "description": "CFO maturity OS — rubric-graded assessments, 12 deliverable chains, 90-day roadmap (Streamlit + Python)",
        "topics": ["cfo", "finance", "fp-a", "ai-agents", "streamlit", "corporate-finance",
                   "maturity-model", "governance"],
    },
    "metabocommand": {
        "description": "Metabolic commerce multi-agent dashboard — capital reflex, approval queues, realtime agent action log (Next.js + Supabase)",
        "topics": ["cfo", "finance", "multi-agent", "ecommerce", "approvals", "supabase",
                   "nextjs", "ai-agents"],
    },
    "meshcfo": {
        "description": "Auditable multi-agent CFO — forecast, investment case, and board packets with CHP provenance",
        "topics": ["cfo", "multi-agent", "finance", "governance", "board-reporting", "chp", "ai-agents"],
    },
    "working-capital-optimizer": {
        "description": "AI agent mesh for AR/AP/inventory — shrink cash conversion cycle with Arize Phoenix eval loop",
        "topics": ["working-capital", "cfo", "cash-conversion-cycle", "ai-agents", "finance", "manufacturing"],
    },
    "cash-flow-optimizer": {
        "description": "13-week cash forecast + daily CFO brief — Xero, Precoro, Outlook, Vellum workflows",
        "topics": ["cash-flow", "cfo", "forecast", "xero", "finance", "ai-agents"],
    },
    "finance-cockpit": {
        "description": "CFO-grade Jira dashboard — budget, burn rate, runway, and working capital (Atlassian Forge)",
        "topics": ["jira", "cfo", "budget", "burn-rate", "atlassian-forge", "finance"],
    },
    "cfo-command-center": {
        "description": "AI finance operations hub built on Notion — CFO agents for cash flow, risk, compliance, and treasury",
        "topics": ["cfo", "notion", "finance", "ai-agents", "treasury", "automation"],
    },
    "solanacfo-treasury": {
        "description": "On-chain Solana treasury management with multi-agent council deliberation (Superteam)",
        "topics": ["solana", "treasury", "defi", "multi-agent", "cfo", "web3"],
    },
    "gotogether-travel-cfo": {
        "description": "Group travel financial orchestration — multi-currency expense splitting, debt simplification, 4-agent council",
        "topics": ["fintech", "travel", "multi-agent", "expense-management", "ai-agents"],
    },
    "software-factory": {
        "description": "Cubiczan stack entry — automated feature factory with MAESTRO security gate and Render previews",
        "topics": ["ai-agents", "devops", "security", "superplane", "software-factory", "maestro"],
    },

    # ---- data, ML & observability ---------------------------------------
    "dataforge-ai": {
        "description": "Production-ML observability agent — watches DataHub lineage, detects silent failures (freshness, schema drift, PSI/KS), writes incidents back",
        "topics": ["mlops", "observability", "datahub", "data-quality", "ai-agents", "python", "lineage"],
    },
    "market-radar": {
        "description": "Jira gadget for market sentiment, Fed policy tracking, and sector rotation — CockroachDB with three-tier data resolution",
        "topics": ["jira", "atlassian-forge", "market-data", "federal-reserve", "cockroachdb", "fintech"],
    },
    "scope-vantage": {
        "description": "Supply chain intelligence platform — HHI concentration risk scoring on AWS Bedrock + Apache Iceberg lakehouse",
        "topics": ["supply-chain", "aws", "bedrock", "iceberg", "risk-analysis", "python", "lakehouse"],
    },
    "chainsight-ai": {
        "description": "AI on-chain anomaly detection for the Mantle Network — six anomaly categories with three-tier data fallback",
        "topics": ["blockchain", "mantle", "anomaly-detection", "ai-agents", "web3", "defi", "python"],
    },
    "geopulse": {
        "description": "GNSS ground-station anomaly detection for disaster early warning in Africa — 5-algorithm engine on ScyllaDB",
        "topics": ["gnss", "anomaly-detection", "disaster-response", "geospatial", "scylladb", "python"],
    },
    "AnnotateX": {
        "description": "LLM data annotation platform — in-context learning, self-consistency decoding, NF4 quantization, semantic S3 cache",
        "topics": ["data-annotation", "llm", "machine-learning", "in-context-learning", "quantization", "python"],
    },

    # ---- security & infrastructure --------------------------------------
    "grid-guardian-intel": {
        "description": "Sentinel-OSINT — cyber-physical threat matrix for US critical infrastructure fusing Censys ICS/SCADA discovery with MITRE ATT&CK",
        "topics": ["osint", "critical-infrastructure", "ics", "scada", "threat-intelligence",
                   "mitre-attack", "censys", "security"],
    },

    # ---- payments & on-chain --------------------------------------------
    "agentpay-v2": {
        "description": "x402 payment layer for AI agents on Casper — GLM-4.6 treasury agent making on-chain spending decisions",
        "topics": ["x402", "casper", "ai-agents", "payments", "blockchain", "treasury", "micropayments"],
    },
    "metal-tokenization-traceability": {
        "description": "MetalX — Solana/Anchor platform tokenizing physical precious-metal reserves with end-to-end batch traceability",
        "topics": ["solana", "anchor", "tokenization", "traceability", "commodities", "rwa", "supply-chain"],
    },
    "swarmfi-preps": {
        "description": "SwarmFi Perps — nine-agent swarm analyzing perpetual futures via dYdX v4 Indexer with persistent stigmergy board",
        "topics": ["defi", "perpetuals", "dydx", "multi-agent", "trading", "swarm-intelligence", "nextjs"],
    },
    "cup-pulse": {
        "description": "P2P fan war room for tournament predictions, watch-parties, and community pledge pipelines — no server in the middle",
        "topics": ["p2p", "web3", "predictions", "sports", "tether", "decentralized"],
    },

    # ---- health & bio ---------------------------------------------------
    "healthguard-ai": {
        "description": "AI healthcare navigator for underserved patients — clinical insights, vitals monitoring, real-time alerts (Gemini XPRIZE)",
        "topics": ["healthcare", "ai-agents", "gemini", "clinical-alerts", "digital-health", "multi-model"],
    },
    "medpsy-clinical-trial-agent": {
        "description": "Clinical trial matching agent — ClinicalTrials.gov search, explainable eligibility, PubMed evidence (Nucleate BioHack)",
        "topics": ["clinical-trials", "healthcare", "ai-agents", "bioinformatics", "pubmed", "llm"],
    },
    "Practice_Radar": {
        "description": "Data-driven target list of 18,095 US healthcare practices — NPPES/CMS pipeline with six-criterion commercial-fit scoring",
        "topics": ["healthcare", "data-pipeline", "lead-generation", "nppes", "python", "sales-ops"],
    },

    # ---- ops & tooling --------------------------------------------------
    "n8n-flows": {
        "description": "Eight scheduled and webhook n8n flows on OSS connectors only — Baserow, SMTP, Mattermost, Nextcloud",
        "topics": ["n8n", "automation", "workflow", "baserow", "self-hosted", "open-source"],
    },
    "modenrich": {
        "description": "Flair Enforcer — auto-flairs Reddit posts with ML classification that learns from mod corrections (Devvit)",
        "topics": ["reddit", "devvit", "machine-learning", "moderation", "classification", "typescript"],
    },
    "Reddit-Community-reply-assistant": {
        "description": "Reddit community reply assistant — buying-intent signal detection and 0–100 thread scoring via snoowrap",
        "topics": ["reddit", "ai-agents", "community-management", "lead-generation", "typescript"],
    },
    "shipkit": {
        "description": "Solo SaaS maker suite — managed auth, billing, analytics, and growth engine so a founder ships in minutes not weeks",
        "topics": ["saas", "starter-kit", "nextjs", "stripe", "authentication", "boilerplate"],
    },

    # ---- topic-only entries (descriptions already good) -----------------
    # These had hand-written descriptions worth keeping but no topics, so only
    # the additive topic sweep applies to them.
    "Live-Diligence": {
        "description": "Autonomous diligence memos from SEC filings — plan/read/scan/synthesize agent loop with dual edge + AWS CDK deployment",
        "topics": ["due-diligence", "sec-edgar", "ai-agents", "finance", "research-automation"],
    },
    "agent-governance": {
        "description": "Governance & audit layer for AI agents that move capital — CHP decision gate, policy engine, HITL approval, signed audit ledger",
        "topics": ["ai-governance", "audit-log", "policy-engine", "hitl", "ai-agents", "typescript", "compliance"],
    },
    "clearance": {
        "description": "Approval, spend-control, and billing layer for production AI agents (Galuxium Nexus V2)",
        "topics": ["ai-agents", "spend-control", "approvals", "billing", "governance", "typescript", "stripe"],
    },
    "capex-draw-tracker": {
        "description": "CIP project tracking, loan draw schedules, and depreciation journals",
        "topics": ["cfo", "finance", "capex", "accounting", "python", "precoro"],
    },
    "close-automation-bot": {
        "description": "Procurement-to-ledger reconciliation and accrual automation for month-end close",
        "topics": ["cfo", "month-end-close", "reconciliation", "accounting", "automation", "python"],
    },
    "commodity-margin-engine": {
        "description": "Index-linked pricing, margin-per-tonne, and sensitivity for commodity processors",
        "topics": ["commodities", "pricing", "finance", "mcp", "python", "margin-analysis"],
    },
    "covenant-compliance-tracker": {
        "description": "Loan covenant monitoring and lender certificate generation from Xero",
        "topics": ["covenant-compliance", "finance", "xero", "lending", "mcp", "python"],
    },
    "invoice-audit-engine": {
        "description": "Continuous vendor invoice anomaly detection for Precoro-based procure-to-pay",
        "topics": ["invoice-audit", "anomaly-detection", "procure-to-pay", "precoro", "mcp", "python"],
    },
    "finance-engines": {
        "description": "Deterministic finance engines for AI agents: commodity margins, covenant compliance, invoice audit — library + MCP server",
        "topics": ["finance", "mcp", "deterministic", "commodities", "covenant-compliance", "javascript"],
    },
    "deltafin": {
        "description": "Automated financial variance analysis for pre-IPO companies — 7-stage pipeline with deterministic variance engine",
        "topics": ["variance-analysis", "cfo", "finance", "pre-ipo", "python", "ai-agents"],
    },
    "stigmergy": {
        "description": "Zero-token multi-agent coordination board: decaying shared signals instead of LLM chat (5.86x faster, 3.4x cheaper)",
        "topics": ["multi-agent", "stigmergy", "coordination", "swarm-intelligence", "typescript", "ai-agents"],
    },
    "incident-commander": {
        "description": "Agentic incident response — 4-agent triage/investigate/resolve/post-mortem pipeline with RAG over runbooks and signed audit ledger",
        "topics": ["incident-response", "sre", "ai-agents", "rag", "observability", "cockroachdb"],
    },
    "consensus-media-gen": {
        "description": "Consensus-verified media generation — multi-model agreement before publish, with 5-phase council deliberation",
        "topics": ["generative-ai", "consensus", "multi-agent", "media-generation", "verification"],
    },
    "keeperhub-agent": {
        "description": "Autonomous on-chain execution agent powered by KeeperHub MCP — price/timer/event triggers via viem",
        "topics": ["mcp", "ai-agents", "blockchain", "automation", "web3", "javascript"],
    },
    "wtf-agent": {
        "description": "WTF-Agent: Web3 Truth & Threat Fusion — confidential threat intelligence on iExec Nox TEE",
        "topics": ["web3", "threat-intelligence", "tee", "iexec", "confidential-computing", "security"],
    },
    "flareintel": {
        "description": "On-chain geopolitical & financial intelligence — Composite Institutional Intelligence scoring on Flare FTSOv2 + FDC attestation",
        "topics": ["flare", "oracle", "geopolitical-risk", "blockchain", "intelligence", "web3"],
    },
    "dyt-marimo": {
        "description": "Reproduction of Dynamic Tanh (Transformers without Normalization, arXiv:2503.10622) as an interactive marimo notebook",
        "topics": ["machine-learning", "transformers", "paper-reproduction", "marimo", "deep-learning", "python"],
    },
    "_cubiczan-shared": {
        "description": "Portfolio tooling — standard-kit injector (AGENTS.md/.chp/resilience) and GitHub metadata sweeper across all repos",
        "topics": ["tooling", "automation", "monorepo-tooling", "governance", "python"],
    },
}


def run(cmd: list[str]) -> tuple[int, str, str]:
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, p.stdout.strip(), p.stderr.strip()


def live_repos() -> dict[str, dict]:
    code, out, err = run(["gh", "repo", "list", ORG, "--limit", "500",
                          "--json", "name,description,repositoryTopics,isFork"])
    if code != 0:
        sys.exit(f"could not list {ORG} repos via gh: {err}\n"
                 f"Is the gh CLI authenticated? Try: gh auth status")
    return {r["name"]: r for r in json.loads(out)}


def validate_topics(name: str, topics: list[str]) -> list[str]:
    problems = []
    if len(topics) > MAX_TOPICS:
        problems.append(f"{len(topics)} topics (max {MAX_TOPICS})")
    for t in topics:
        if not t.replace("-", "").isalnum() or t != t.lower() or len(t) > 50:
            problems.append(f"invalid topic {t!r}")
    if problems:
        print(f"  ! {name}: {'; '.join(problems)}")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true",
                    help="actually write; omitting this is a dry-run")
    ap.add_argument("--repos", help="comma-separated subset to update")
    ap.add_argument("--overwrite-descriptions", action="store_true",
                    help="replace existing descriptions instead of only filling empty ones")
    args = ap.parse_args()

    live = live_repos()
    wanted = set(REPOS)
    if args.repos:
        wanted &= {r.strip() for r in args.repos.split(",") if r.strip()}
        if not wanted:
            return sys.exit("--repos matched nothing in REPOS")

    # Validate before touching anything: a name typo or bad topic should be a
    # report, not a half-finished sweep.
    unknown = sorted(n for n in wanted if n not in live)
    if unknown:
        print(f"! not found in {ORG} (skipping): {', '.join(unknown)}\n")
        wanted -= set(unknown)

    bad = False
    for name in sorted(wanted):
        meta = REPOS[name]
        if len(meta["description"]) > MAX_DESCRIPTION:
            print(f"  ! {name}: description {len(meta['description'])} chars "
                  f"(max {MAX_DESCRIPTION})")
            bad = True
        if validate_topics(name, meta["topics"]):
            bad = True
    if bad:
        return 1

    planned, skipped = [], []
    for name in sorted(wanted):
        cur = live[name]
        if cur["isFork"]:
            skipped.append((name, "fork — upstream metadata left alone"))
            continue
        has_desc = bool((cur["description"] or "").strip())
        cur_topics = {t["name"] for t in (cur["repositoryTopics"] or [])}
        new_topics = set(REPOS[name]["topics"]) - cur_topics
        set_desc = not has_desc or args.overwrite_descriptions
        if not set_desc and not new_topics:
            skipped.append((name, "description present, no new topics"))
            continue
        planned.append((name, set_desc, sorted(new_topics)))

    mode = "APPLY" if args.apply else "DRY-RUN (pass --apply to write)"
    print(f"{mode} — {len(planned)} repo(s) to update, {len(skipped)} skipped\n")

    for name, why in skipped:
        print(f"  · {name}: {why}")
    if skipped:
        print()

    failures = 0
    for name, set_desc, new_topics in planned:
        meta = REPOS[name]
        cur_desc = (live[name]["description"] or "").strip()
        print(f"  {name}")
        if set_desc:
            was = "(none)" if not cur_desc else f"{cur_desc[:58]}…"
            print(f"      description: {was}")
            print(f"               -> {meta['description']}")
        elif cur_desc:
            print(f"      description: kept — {cur_desc[:58]}…")
        if new_topics:
            print(f"      + topics: {', '.join(new_topics)}")

        if not args.apply:
            continue

        if set_desc:
            code, _, err = run(["gh", "repo", "edit", f"{ORG}/{name}",
                                "--description", meta["description"]])
            if code != 0:
                print(f"      ✗ description failed: {err}")
                failures += 1
                continue
        if new_topics:
            topic_args: list[str] = []
            for t in new_topics:
                topic_args += ["--add-topic", t]
            code, _, err = run(["gh", "repo", "edit", f"{ORG}/{name}"] + topic_args)
            if code != 0:
                print(f"      ✗ topics failed: {err}")
                failures += 1
                continue
        print("      ✓ updated")

    if failures:
        print(f"\n{failures} repo(s) failed")
        return 1
    if args.apply:
        print(f"\ndone — {len(planned)} repo(s) updated")
    else:
        print("\nnothing written. Re-run with --apply.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
