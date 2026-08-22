> **Status:** Absorbed into [`consensus-hardening-protocol`](https://github.com/icohangar-ops/consensus-hardening-protocol).
> The `.chp` kit injector from this repo is now `chp init` there — use `pip install consensus-hardening-protocol` (and for TypeScript Profile B: `npm install @cubiczan/chp`).
> This repository is kept for history and will be archived.

# _cubiczan-shared

Portfolio-wide tooling. This repo holds no product code — it holds the scripts that keep
~120 sibling repos converging on the same contract, plus the canonical text of the
Cubiczan stack blurb that gets injected into their READMEs.

The leading underscore marks it as infrastructure, alongside `_cubiczan-updates` and
`_AUDIT`. `inject_stack.py` deliberately excludes all three from its own sweep.

| File | What it is |
|---|---|
| [`CUBICZAN_STACK.md`](CUBICZAN_STACK.md) | Canonical stack blurb injected into sibling READMEs, plus the standard-kit docs |
| [`inject_stack.py`](inject_stack.py) | Seeds each sibling repo with the standard kit (README header, `AGENTS.md`, `.chp/`, resilience reference) |
| [`update_github_meta.py`](update_github_meta.py) | Sets GitHub descriptions and topics across the org |

Both scripts are stdlib-only Python and **dry-run by default**. Neither writes anything
until you pass `--apply`.

## Standard-kit injector

```bash
python3 inject_stack.py                       # dry-run across every sibling repo
python3 inject_stack.py --selfcheck           # show detected language per repo
python3 inject_stack.py --kit agents,chp --repos meshcfo,cleanmandate --apply
python3 inject_stack.py --kit resilience --apply
```

Kit parts: `readme` (opt-in), `agents`, `chp`, `resilience`. Idempotent — re-running skips
files that already exist. `--force` overwrites managed files. Full behaviour, including how
the resilience part detects each repo's language, is documented in
[`CUBICZAN_STACK.md`](CUBICZAN_STACK.md#standard-kit-inject_stackpy).

## GitHub metadata sweeper

Fixes the discoverability gap found in the July 2026 portfolio audit: 26 repos had no
description at all — including the highest-reach repo in the dependency graph — and only 12
carried topics.

```bash
python3 update_github_meta.py                 # dry-run
python3 update_github_meta.py --apply         # fill gaps
python3 update_github_meta.py --apply --repos market-radar,geopulse
python3 update_github_meta.py --apply --overwrite-descriptions
```

Safe in three ways beyond the dry-run default:

- **Existing descriptions are kept.** A hand-written description beats a generated one, so
  the tool only fills empty ones unless you explicitly pass `--overwrite-descriptions`.
- **Topics are additive.** It computes the set difference and adds only what's missing, so
  curated topics are never dropped.
- **Names are validated first** against the live org listing, so a typo is reported up
  front rather than 404ing halfway through a sweep.

Auth comes from the `gh` CLI, which is already authenticated. No token is read, stored, or
passed on a command line — so nothing here can leak one. If `gh` isn't authenticated the
tool says so and exits.

## Adding a repo to the sweeper

Add an entry to `REPOS` in `update_github_meta.py`:

```python
"my-repo": {
    "description": "One line a stranger can identify the repo from. Under 350 chars.",
    "topics": ["lowercase-hyphenated", "max-20-of-them"],
},
```

Then dry-run. Topics must be lowercase alphanumeric plus hyphens, at most 50 characters
each and 20 per repo — GitHub rejects the whole call otherwise, so the tool validates
before writing anything.
