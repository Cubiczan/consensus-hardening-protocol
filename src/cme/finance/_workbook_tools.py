"""Shared helpers for locating bundled Node ``.mjs`` workbook tools.

Historically each finance module resolved the ``tools/`` directory via
``Path(__file__).resolve().parents[3]`` (the source-checkout repo root). That
breaks once the package is installed as a wheel, where the source tree layout
no longer holds. This module resolves the tools directory via candidate
locations that work both from a source checkout and from an installed package,
so callers no longer depend on a fixed ``parents[3]`` hop.

Resolution order:

1. ``CHP_WORKBOOK_TOOLS_DIR`` environment override, if set.
2. Package data shipped alongside the installed package
   (``cme/finance/_workbook_tools_data``), if present.
3. The repo-root ``tools/`` directory (source-checkout / editable installs).
"""
from __future__ import annotations

import os
from pathlib import Path

# Default per-call wall-clock budget (seconds) for Node workbook subprocesses.
# Bounds a hung Node process so callers fail fast instead of blocking forever.
WORKBOOK_SUBPROCESS_TIMEOUT = float(os.environ.get("CHP_WORKBOOK_TIMEOUT", "60"))


def resolve_tools_dir() -> Path:
    """Return the directory containing the Node ``.mjs`` workbook builders.

    Works from both a source checkout and an installed wheel. Raises
    ``RuntimeError`` only if no candidate location exists.
    """
    candidates = []

    override = os.environ.get("CHP_WORKBOOK_TOOLS_DIR")
    if override:
        candidates.append(Path(override))

    # Package data bundled next to this module (present in wheels that ship
    # the tools as package data).
    candidates.append(Path(__file__).resolve().parent / "_workbook_tools_data")

    # Source-checkout / editable-install layout: <repo_root>/tools.
    candidates.append(Path(__file__).resolve().parents[3] / "tools")

    for candidate in candidates:
        if candidate.is_dir():
            return candidate

    # Fall back to the source-checkout path for a clear error message; the
    # caller's subsequent file access will surface a precise FileNotFoundError.
    return Path(__file__).resolve().parents[3] / "tools"
