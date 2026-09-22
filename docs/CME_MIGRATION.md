# Status of `src/cme/` in this repository

This repository now publishes **one** package: `consensus-hardening-protocol`
(import name `chp`, source in `src/chp/`). `src/cme/` — the 11,387-LOC Cognitive
Mesh project that used to be the point of this repo — is still here but is **no
longer packaged**. `pyproject.toml` includes only `chp*`.

Its long-term home is `stratifi-core`, whose own description is "Stratifi Core
packages the Cognitive Mesh Enterprise Orchestrator (cme)". It was left in place
rather than moved because the move is not a copy.

## The two `cme` trees have diverged in both directions

Compared 2026-08-21, file by file. `stratifi-core` is **not** a superset, so
deleting `src/cme/` here would lose work.

Only in **this** repo:

| File | Lines | Note |
|---|---:|---|
| `finance/_workbook_tools.py` | 52 | exists nowhere else |

Larger in **this** repo than in `stratifi-core`:

| File | here | stratifi-core |
|---|---:|---:|
| `cli.py` | 1,282 | 360 |
| `cashflow_13w.py` | 744 | 723 |
| `investment_committee.py` | 439 | 430 |
| `saas_operating_model.py` | 540 | 531 |
| `saas_kpi_dashboard.py` | 637 | 628 |
| `ap_optimizer.py` | 694 | 685 |
| `board_reporting.py` | 358 | 349 |
| `cfo_os/orchestrator.py` | 336 | 287 |

Only in **stratifi-core**: `db/` (2 files, 147 lines), `research/` (4 files,
1,610 lines), `finance/variance_forecast.py` (445), `finance/variance_mom.py`
(589). Its `cfo_os/*` and `finance/__init__.py` are also larger.

## Consequence

Migrating `cme` requires a real two-way merge of two 11k-LOC trees, decided
module by module. That is its own piece of work and deliberately not part of the
package consolidation.

## Legacy tests

The 15 test files directly under `tests/` are `cme` tests. They already failed
to collect before this change — 13 collection errors, from dependencies that
were never installable (the old `pyproject.toml` required `cubiczan-resilience`
through a git URL, which is also why the project could never be published to
PyPI). They are untouched here.

CI runs `tests/chp` only, so the package's suite is green and deterministic.
Fixing the `cme` suite belongs with the migration above.
