#!/usr/bin/env python3
"""Cubiczan standard-kit injector.

Originally: inject the Cubiczan stack header + footer into a repo README.
Now also the rollout vehicle for the portfolio-wide "standard kit" — one
scripted sweep seeds each sibling repo with governance + resilience scaffolding:

  readme      Cubiczan stack header + footer in README.md (original behavior)
  agents      AGENTS.md contract (generalized from agent-conductor)
  chp         .chp/ decision-governance scaffold (policy.yaml + README.md)
  resilience  a dependency reference to cubiczan-resilience for the repo's language
  evidence    the evidence-matrix gate: vendored stamped verifier + scaffold
              matrix + required CI job (opt-in — the scaffold is failing by design)

Plain Python, stdlib only. Safe by default: DRY-RUN unless you pass --apply.
Never clobbers existing files unless you pass --force. Idempotent.

Examples
--------
  # See what a full sweep would do to every sibling repo (dry-run):
  python inject_stack.py

  # Only the AGENTS.md + .chp kit, still dry-run:
  python inject_stack.py --kit agents,chp

  # Actually write the resilience reference into three named repos:
  python inject_stack.py --kit resilience --repos meshcfo,cleanmandate,cash-flow-optimizer --apply

  # Overwrite an existing AGENTS.md in one repo:
  python inject_stack.py --kit agents --repos metabocommand --apply --force
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

SHARED = Path(__file__).resolve().parent
REPOS_ROOT = SHARED.parent  # /Users/cubiczan/Desktop/icohangar-repos
RESILIENCE_ROOT = REPOS_ROOT / "cubiczan-resilience"

STACK = SHARED / "CUBICZAN_STACK.md"
# Only the portion above this marker is injected into repo READMEs; everything
# after it is internal tooling documentation that should not leak into READMEs.
_FOOTER_MARKER = "<!-- END:README_FOOTER"
STACK_TEXT = STACK.read_text().split(_FOOTER_MARKER, 1)[0].rstrip() + "\n"

# ---------------------------------------------------------------------------
# README injection (original behavior, unchanged in spirit)
# ---------------------------------------------------------------------------

HEADER_TMPL = (
    "\n> **Cubiczan stack** — [Profile](https://github.com/Cubiczan) · "
    "[software-factory](https://github.com/Cubiczan/software-factory) · "
    "**You are here:** `{repo}`\n"
)


def inject_readme(repo: str, repo_dir: Path, *, apply: bool, force: bool) -> str:
    """Inject stack header + footer into repo_dir/README.md. Returns a status token."""
    path = repo_dir / "README.md"
    if not path.exists():
        return "skip (no README.md)"
    text = path.read_text()
    if "## Cubiczan stack" in text and not force:
        return "skip (already has stack section)"

    header = HEADER_TMPL.format(repo=repo)
    lines = text.splitlines(keepends=True)
    out = []
    inserted_header = False
    for line in lines:
        out.append(line)
        if not inserted_header and line.startswith("#"):
            out.append(header)
            inserted_header = True
    text = "".join(out)

    marker = "\n## License\n"
    if marker in text:
        text = text.replace(marker, "\n---\n\n" + STACK_TEXT + "\n" + marker, 1)
    else:
        text = text.rstrip() + "\n\n---\n\n" + STACK_TEXT + "\n"

    if apply:
        path.write_text(text)
        return "WROTE README.md"
    return "would write README.md"


# ---------------------------------------------------------------------------
# AGENTS.md contract template (generalized from agent-conductor)
# ---------------------------------------------------------------------------

AGENTS_TMPL = """# AGENTS.md — {repo}

Guidance for AI coding agents working in this repository. This contract is
config-driven governance generalized from the Cubiczan standard kit; it is
designed to compile with Agent Conductor (`contract_load` on this file).

## Mission

<!-- One paragraph: what this repo does and the invariants agents must protect.
     Replace this placeholder before relying on the contract. -->
{repo} is part of the Cubiczan stack of auditable AI for finance and
governance. Keep the dependency surface small, keep decisions traceable to
policy + reasoning + human approval, and never silently weaken a safety gate.

## Architecture

| Layer | Role | Do | Don't |
|-------|------|----|-------|
| `src/` | Core logic | Keep modules cohesive and testable | Reach across layer boundaries |
| `.chp/` | Decision governance | Route high-stakes actions through the CHP policy | Bypass gates for convenience |
| `test/` | Regression guard | Test against real fixtures | Mock away the behavior under test |

## Engineering rules

### Non-negotiables

1. **Traceable decisions** — high-stakes actions pass through the `.chp/` policy (see `.chp/README.md`).
2. **Resilience by default** — external calls use `cubiczan-resilience` (timeout + retry/backoff); money/state operations are idempotent.
3. **No silent gate weakening** — changing a `.chp/policy.yaml` threshold or an approval requirement is a reviewed change, never a drive-by.
4. **Conservative dependencies** — justify every new runtime dependency.
5. **Deterministic, replayable tests** — no network in unit tests.

### Code change checklist

```bash
# Fill in the repo's real commands:
# <lint>
# <type-check>
# <test>
```

## Out of scope (unless explicitly requested)

- Changing governance policy defaults without review
- Introducing new external services without a resilience wrapper
"""


def inject_agents(repo: str, repo_dir: Path, *, apply: bool, force: bool) -> str:
    path = repo_dir / "AGENTS.md"
    if path.exists() and not force:
        return "skip (AGENTS.md exists)"
    content = AGENTS_TMPL.format(repo=repo)
    if apply:
        path.write_text(content)
        return "WROTE AGENTS.md" + (" (forced)" if path.exists() and force else "")
    verb = "would overwrite" if path.exists() else "would write"
    return f"{verb} AGENTS.md"


# ---------------------------------------------------------------------------
# .chp/ decision-governance scaffold
# ---------------------------------------------------------------------------

CHP_POLICY_YAML = """# .chp/policy.yaml — Consensus Hardening Protocol decision policy
# Config-driven governance. Tune thresholds per repo; changes here are reviewed.
version: 1

# A decision is "high-stakes" when any matching signal fires. High-stakes
# decisions require adversarial review and, above the escalation threshold,
# human approval before the action is taken.
signals:
  money_movement: true          # payments, transfers, refunds, mandates
  irreversible_state: true      # deletes, migrations, prod config writes
  external_publish: true        # anything that leaves the trust boundary
  security_relevant: true       # auth, secrets, permissions, allowlists

thresholds:
  # Probabilistic confidence required to auto-proceed without escalation.
  auto_proceed_confidence: 0.85
  # Below this, escalate to a human approval queue.
  escalate_below_confidence: 0.70

review:
  adversarial: true             # run an adversarial/critic pass
  min_reviewers: 1              # independent review passes before lock
  require_human_approval_for:
    - money_movement
    - irreversible_state

audit:
  record: true                  # emit a signed, replayable decision record
  sink: ".chp/audit/"           # where decision records are written
"""

CHP_README = """# .chp/ — Consensus Hardening Protocol config

This directory holds the **decision-governance config** for this repo. It is the
local, config-driven expression of the Cubiczan CHP: high-stakes actions are
gated by adversarial review, probabilistic confidence, and (when required)
human approval, with a signed audit trail.

## Files

- `policy.yaml` — which decisions are high-stakes, the confidence thresholds,
  what requires human approval, and where audit records go.

## How it is used

Agents and services consult `policy.yaml` before taking an action:

1. Classify the action against `signals`.
2. If high-stakes, run the required `review` passes.
3. Compare confidence to `thresholds`; escalate to a human queue if below the
   escalation threshold or if the signal is on `require_human_approval_for`.
4. Emit a decision record under `audit.sink`.

The canonical engine lives in
[consensus-hardening-protocol](https://github.com/Cubiczan/consensus-hardening-protocol)
and is orchestrated by
[agent-conductor](https://github.com/Cubiczan/agent-conductor). This config is
what makes the gate real for *this* repo — keep it honest.

## Changing this policy

Loosening a threshold or removing an approval requirement is a reviewed change,
never a drive-by. See `AGENTS.md` non-negotiable #3.
"""


def inject_chp(repo: str, repo_dir: Path, *, apply: bool, force: bool) -> str:
    chp_dir = repo_dir / ".chp"
    policy = chp_dir / "policy.yaml"
    readme = chp_dir / "README.md"
    existing = [p.name for p in (policy, readme) if p.exists()]

    if existing and not force:
        return f"skip (.chp exists: {', '.join(existing)})"

    if apply:
        chp_dir.mkdir(exist_ok=True)
        policy.write_text(CHP_POLICY_YAML)
        readme.write_text(CHP_README)
        return "WROTE .chp/policy.yaml + .chp/README.md" + (
            " (forced)" if existing else ""
        )
    verb = "would overwrite" if existing else "would write"
    return f"{verb} .chp/policy.yaml + .chp/README.md"


# ---------------------------------------------------------------------------
# Resilience-dependency injector
# ---------------------------------------------------------------------------

# Prefer the strongest / most specific manifest first when a repo is polyglot.
LANG_MANIFESTS = [
    ("rust", "Cargo.toml"),
    ("ts", "package.json"),
    ("python", "pyproject.toml"),
    ("python", "requirements.txt"),
]

RESILIENCE_PKG = {
    "ts": "@cubiczan/resilience",
    "python": "cubiczan-resilience",
    "rust": "resilient-call",
}


def detect_language(repo_dir: Path) -> tuple[str | None, str | None]:
    """Return (language, manifest_filename) or (None, None)."""
    for lang, manifest in LANG_MANIFESTS:
        if (repo_dir / manifest).exists():
            return lang, manifest
    return None, None


def _rel_local_path(repo_dir: Path, sub: str) -> str:
    """A local filesystem path from repo_dir to the resilience sub-package."""
    import os

    target = RESILIENCE_ROOT / sub
    try:
        return os.path.relpath(target, repo_dir)
    except ValueError:
        return str(target)


def _already_has_resilience(text: str) -> bool:
    return any(
        tok in text
        for tok in ("cubiczan-resilience", "@cubiczan/resilience", "resilient-call")
    )


def inject_resilience(repo: str, repo_dir: Path, *, apply: bool, force: bool) -> str:
    lang, manifest = detect_language(repo_dir)
    if lang is None:
        return "skip (no recognized manifest)"

    manifest_path = repo_dir / manifest
    text = manifest_path.read_text()
    if _already_has_resilience(text) and not force:
        return f"skip ({lang}: {manifest} already references resilience)"

    pkg = RESILIENCE_PKG[lang]

    # We do NOT edit the manifest structurally (too easy to break TOML/JSON
    # semantics conservatively). Instead we append a clearly-marked, documented
    # local-path reference note as a comment where the format allows, plus write
    # a sibling ADOPT note. This is safe and reversible; the user wires the real
    # dependency in deliberately.
    note_path = repo_dir / "RESILIENCE_ADOPT.md"

    if lang == "rust":
        local = _rel_local_path(repo_dir, "rust")
        snippet = (
            f'# cubiczan standard kit: add the resilience crate. Publishing is not\n'
            f'# set up yet, so reference it locally (or via git once published):\n'
            f'# [dependencies]\n'
            f'# {pkg} = {{ path = "{local}" }}\n'
        )
        adopt = (
            f"# Adopt cubiczan-resilience ({pkg})\n\n"
            f"Rust crate. Until it is published to crates.io, add to `Cargo.toml`:\n\n"
            f"```toml\n[dependencies]\n{pkg} = {{ path = \"{local}\" }}\n```\n\n"
            f"Then use timeout / backoff+jitter / CockroachDB serializable-retry "
            f"(SQLSTATE 40001) / idempotency-ledger helpers.\n"
        )
    elif lang == "ts":
        local = _rel_local_path(repo_dir, "typescript")
        snippet = (
            f'  "//cubiczan-resilience": "add {pkg} — local path until published: '
            f'file:{local}"\n'
        )
        adopt = (
            f"# Adopt cubiczan-resilience ({pkg})\n\n"
            f"TypeScript. Until it is published to npm, reference it locally:\n\n"
            f"```jsonc\n// package.json dependencies\n"
            f'"{pkg}": "file:{local}"\n```\n\n'
            f"Provides `safeFetch()` (timeout + retry/backoff + SSRF allowlist) and "
            f"`requireAuth()` (fail-closed bearer + rate limit).\n"
        )
    else:  # python
        local = _rel_local_path(repo_dir, "python")
        if manifest == "requirements.txt":
            snippet = (
                f"# cubiczan standard kit: resilience library. Not on PyPI in this\n"
                f"# environment — reference the local checkout (editable):\n"
                f"# -e {local}\n"
            )
        else:  # pyproject.toml
            snippet = (
                f'# cubiczan standard kit: add "{pkg}" to dependencies. Until it is\n'
                f'# published, use a local path dependency, e.g. with uv/hatch:\n'
                f'#   {pkg} @ {{ path = "{local}" }}\n'
            )
        adopt = (
            f"# Adopt cubiczan-resilience ({pkg})\n\n"
            f"Python. Until it is published to PyPI, install the local checkout:\n\n"
            f"```bash\npip install -e {local}\n```\n\n"
            f"Provides `@resilient` (timeout + backoff-with-jitter + circuit breaker), "
            f"an idempotency-key store, atomic file write, and a FastAPI auth "
            f"dependency + CORS allowlist factory.\n"
        )

    if apply:
        # Conservative: append a comment to the manifest only for comment-capable
        # formats (Cargo.toml, requirements.txt, pyproject.toml). For package.json
        # (JSON, no comments) we DO NOT touch the manifest — only the ADOPT note.
        touched = []
        if manifest in ("Cargo.toml", "requirements.txt", "pyproject.toml"):
            if snippet.strip() not in text:
                manifest_path.write_text(text.rstrip() + "\n\n" + snippet)
                touched.append(manifest)
        note_path.write_text(adopt)
        touched.append("RESILIENCE_ADOPT.md")
        return f"WROTE resilience note [{lang}] -> {', '.join(touched)}"

    if manifest == "package.json":
        return (
            f"would write RESILIENCE_ADOPT.md [{lang}] "
            f"(JSON manifest left untouched; wire {pkg} = file:{local})"
        )
    return (
        f"would append resilience note to {manifest} + write RESILIENCE_ADOPT.md "
        f"[{lang}] (ref {pkg})"
    )


# ---------------------------------------------------------------------------
# Evidence-matrix gate
# ---------------------------------------------------------------------------

# The vendored copy is written BYTES-IDENTICAL from the kit's canonical file so
# drift stays a one-line diff (see CUBICZAN_STACK.md, "Evidence matrix").
_CANONICAL_VERIFIER = SHARED / "tools" / "verify_evidence_matrix.py"

EVIDENCE_MATRIX_SCAFFOLD = """# evidence/matrix.yaml — every capability claim bound to deterministic evidence.
# Scaffold written by the Cubiczan standard kit (inject_stack.py --kit evidence).
# Replace with real rows: inventory the README/docs capability claims section by
# section, and bind each one to evidence that exists in this tree — or reword the
# claim to what is true, visibly. CI fails while this file has no claims: an
# empty matrix is not decision-ready.
#
# Row shape (schema v1 — canonical verifier: tools/verify_evidence_matrix.py,
# canonical kit: icohangar-ops/consensus-hardening-protocol):
#
# - id: C001                      # unique, stable, C-prefixed
#   claim: >-                     # verbatim or tight paraphrase of the stated claim
#     The stated capability, in one sentence.
#   source: "README.md#features"  # locator where the claim is made; the file must exist
#   evidence:                     # >= 1 ref; empty list is a failure
#     - type: test                # test | script | manifest_field | artifact_hash
#       ref: "tests/test_core.py::test_feature"
#     - type: script
#       ref: "scripts/verify_feature.sh"
#       timeout_seconds: 120
#     - type: manifest_field
#       ref: "manifest.json:claims.parameters"
#       equals:                   # pinned value the dotted path must equal
#         hubspot_weight: 0.4
#     - type: artifact_hash
#       ref: "data/seed.csv"
#       sha256: "64-hex-chars pinning the exact committed bytes"
schema_version: 1
repo: __REPO__
claims: []
"""

EVIDENCE_WORKFLOW_YAML = """# Evidence-matrix gate — seeded by the Cubiczan standard kit
# (canonical kit: icohangar-ops/consensus-hardening-protocol). Refuses the build
# while any claim in
# evidence/matrix.yaml is unverifiable. Required: a red matrix job means the
# README's capability claims are not evidence-backed. No secrets, no services.
name: evidence-matrix

on:
  pull_request:
  push:
    branches: [main]

jobs:
  evidence-matrix:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: python3 tools/verify_evidence_matrix.py
"""

EVIDENCE_README_SECTION = """## Evidence matrix

Every capability claim in this file is backed by
[`evidence/matrix.yaml`](evidence/matrix.yaml); CI refuses builds while any row
is unverifiable (run `python3 tools/verify_evidence_matrix.py` locally).
"""


def inject_evidence(repo: str, repo_dir: Path, *, apply: bool, force: bool) -> str:
    """Seed the evidence-matrix gate: stamped verifier + scaffold matrix + CI job."""
    if not _CANONICAL_VERIFIER.is_file():
        return "skip (kit is missing tools/verify_evidence_matrix.py — canonical verifier absent)"

    targets = [
        (repo_dir / "tools" / "verify_evidence_matrix.py", _CANONICAL_VERIFIER.read_bytes()),
        (repo_dir / "evidence" / "matrix.yaml", EVIDENCE_MATRIX_SCAFFOLD.replace("__REPO__", repo).encode("utf-8")),
        (repo_dir / ".github" / "workflows" / "evidence-matrix.yml", EVIDENCE_WORKFLOW_YAML.encode("utf-8")),
    ]
    existing = [t for t, _ in targets if t.exists()]
    if existing and not force:
        return f"skip (evidence files exist: {', '.join(str(t.relative_to(repo_dir)) for t in existing)})"

    if apply:
        for path, content in targets:
            if path.exists() and not force:
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        readme_touched = False
        readme = repo_dir / "README.md"
        # The norm section is add-if-missing, never forced — README prose is
        # the author's; the injector only adds the contract sentence once.
        if readme.is_file() and "## Evidence matrix" not in readme.read_text():
            readme.write_text(readme.read_text().rstrip() + "\n" + EVIDENCE_README_SECTION)
            readme_touched = True
        status = "WROTE evidence-matrix gate (stamped verifier + scaffold matrix + CI job"
        if readme_touched:
            status += " + README section"
        status += ")"
        if existing:
            status += " (forced)"
        return status

    verb = "would overwrite" if existing else "would write"
    return (
        f"{verb} evidence-matrix gate: tools/verify_evidence_matrix.py "
        "+ evidence/matrix.yaml + .github/workflows/evidence-matrix.yml"
    )


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

KIT_PARTS = {
    "readme": inject_readme,
    "agents": inject_agents,
    "chp": inject_chp,
    "resilience": inject_resilience,
    "evidence": inject_evidence,
}
DEFAULT_KIT = ["agents", "chp", "resilience"]

# Directories under REPOS_ROOT that are not target repos.
NON_REPO_DIRS = {
    "consensus-hardening-protocol",  # the kit home; don't inject into itself
    "_cubiczan-shared",  # archived former kit home
    "_cubiczan-updates",
    "_AUDIT",
    "cubiczan-resilience",  # the source of truth; don't inject into itself
}


def discover_repos() -> list[str]:
    repos = []
    for p in sorted(REPOS_ROOT.iterdir()):
        if not p.is_dir():
            continue
        if p.name.startswith("."):
            continue
        if p.name in NON_REPO_DIRS:
            continue
        repos.append(p.name)
    return repos


def run(repos: list[str], kit: list[str], *, apply: bool, force: bool) -> None:
    mode = "APPLY" if apply else "DRY-RUN"
    print(f"=== Cubiczan standard-kit injector [{mode}] ===")
    print(f"kit: {', '.join(kit)}   repos: {len(repos)}"
          f"   force: {force}\n")

    changes = 0
    for repo in repos:
        repo_dir = REPOS_ROOT / repo
        if not repo_dir.is_dir():
            print(f"{repo}")
            print(f"    MISSING repo dir: {repo_dir}")
            continue
        print(f"{repo}")
        for part in kit:
            fn = KIT_PARTS[part]
            status = fn(repo, repo_dir, apply=apply, force=force)
            if status.startswith(("WROTE", "would")):
                changes += 1
            print(f"    [{part:10}] {status}")
    print(f"\n=== {changes} change(s) {'applied' if apply else 'pending'} "
          f"({mode}) ===")
    if not apply and changes:
        print("Re-run with --apply to write these changes.")


def selfcheck() -> None:
    """Language-detection self-check across a few sibling repos."""
    print("=== language detection self-check ===")
    for repo in discover_repos():
        repo_dir = REPOS_ROOT / repo
        lang, manifest = detect_language(repo_dir)
        if lang:
            print(f"  {repo:40} -> {lang:7} ({manifest})")


def parse_args(argv: list[str]) -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description="Cubiczan standard-kit injector.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument(
        "--kit",
        default=",".join(DEFAULT_KIT),
        help=(
            "comma-separated parts to inject: "
            f"{', '.join(KIT_PARTS)} (default: {','.join(DEFAULT_KIT)})"
        ),
    )
    ap.add_argument(
        "--repos",
        default="",
        help="comma-separated repo names (default: all sibling repos)",
    )
    ap.add_argument(
        "--apply",
        action="store_true",
        help="actually write changes (default is dry-run)",
    )
    ap.add_argument(
        "--force",
        action="store_true",
        help="overwrite existing files instead of skipping",
    )
    ap.add_argument(
        "--selfcheck",
        action="store_true",
        help="print detected language per sibling repo and exit",
    )
    ap.add_argument(
        "--list-repos",
        action="store_true",
        help="print discovered sibling repos and exit",
    )
    return ap.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)

    if args.list_repos:
        for r in discover_repos():
            print(r)
        return 0
    if args.selfcheck:
        selfcheck()
        return 0

    kit = [k.strip() for k in args.kit.split(",") if k.strip()]
    unknown = [k for k in kit if k not in KIT_PARTS]
    if unknown:
        print(f"error: unknown kit part(s): {', '.join(unknown)}", file=sys.stderr)
        print(f"valid parts: {', '.join(KIT_PARTS)}", file=sys.stderr)
        return 2

    if args.repos:
        repos = [r.strip() for r in args.repos.split(",") if r.strip()]
    else:
        repos = discover_repos()

    run(repos, kit, apply=args.apply, force=args.force)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
