"""Command line entry point for the Consensus Hardening Protocol.

``chp init`` seeds a repository with the canonical ``.chp/`` governance kit —
the R0 gate configuration, the adversarial prompt set, the state machine and the
compliance checklist. It replaces the portfolio-wide ``inject_stack.py`` sweep
and keeps that tool's contract: dry-run unless you pass ``--apply``, never
clobber an existing file unless you pass ``--force``, and safe to re-run.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    from importlib.resources import files as _res_files
except ImportError:  # pragma: no cover - Python < 3.9
    _res_files = None  # type: ignore[assignment]

KIT_FILES = (
    "R0_CONFIG.yaml",
    "ADVERSARIAL_PROMPTS.md",
    "STATE_MACHINE.md",
    "CHP_COMPLIANCE.md",
)


def _kit_source(name: str) -> str:
    if _res_files is None:  # pragma: no cover
        return (Path(__file__).parent / "kit" / name).read_text()
    return (_res_files("chp") / "kit" / name).read_text(encoding="utf-8")


def cmd_init(args: argparse.Namespace) -> int:
    target = Path(args.path).resolve()
    if not target.is_dir():
        print(f"error: {target} is not a directory", file=sys.stderr)
        return 2

    chp_dir = target / ".chp"
    planned: list[tuple[str, str]] = []
    for name in KIT_FILES:
        dest = chp_dir / name
        if dest.exists() and not args.force:
            planned.append((name, "skip (exists)"))
        else:
            planned.append((name, "overwrite" if dest.exists() else "create"))

    verb = "writing" if args.apply else "would write"
    print(f"{verb} .chp/ kit in {target}")
    for name, action in planned:
        print(f"  {action:18s} .chp/{name}")

    if not args.apply:
        print("\ndry run — nothing written. Re-run with --apply.")
        return 0

    chp_dir.mkdir(exist_ok=True)
    written = 0
    for name, action in planned:
        if action.startswith("skip"):
            continue
        (chp_dir / name).write_text(_kit_source(name), encoding="utf-8")
        written += 1
    print(f"\nwrote {written} file(s) to {chp_dir}")
    if written == 0:
        print("nothing to do — pass --force to replace existing files.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="chp", description="Consensus Hardening Protocol tooling."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="seed a repository with the .chp/ governance kit")
    init.add_argument("path", nargs="?", default=".", help="repository root (default: .)")
    init.add_argument("--apply", action="store_true", help="actually write files")
    init.add_argument("--force", action="store_true", help="replace existing files")
    init.set_defaults(func=cmd_init)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
