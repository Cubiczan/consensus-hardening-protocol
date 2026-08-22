"""Regression tests for D-A1 — domain-aware foundation floors (spec §5.3).

The canonical port hardcoded 70 for every domain, so a finance decision scoring
70 cleared a gate documented as requiring 100. These tests pin the normative
behaviour and keep the engine aligned with spec/conformance/chp_reference.py.
"""
from __future__ import annotations

import logging

import pytest

from chp.foundation import (
    DEFAULT_FOUNDATION_FLOOR,
    FOUNDATION_FLOORS,
    foundation_floor,
    foundation_verdict,
)
from chp.models import FoundationAttack, Verdict


def _attack(score: int) -> FoundationAttack:
    return FoundationAttack(
        assumption_attacks=["a", "b", "c"],
        vulnerability_strike="strike",
        foundation_score=score,
    )


@pytest.mark.parametrize(
    "domain,floor",
    [
        ("general", 70), ("ai", 70), ("agents", 70),
        ("blockchain", 85), ("defi", 85),
        ("finance", 100), ("cfo", 100),
        ("capital_allocation", 100), ("board_decision", 100),
    ],
)
def test_floor_matches_spec_table(domain: str, floor: int) -> None:
    assert foundation_floor(domain) == floor


@pytest.mark.parametrize("domain", ["", None, "unlisted", "marketing"])
def test_unlisted_domain_falls_back_to_default_not_zero(domain) -> None:
    assert foundation_floor(domain) == DEFAULT_FOUNDATION_FLOOR


def test_floor_is_case_insensitive() -> None:
    assert foundation_floor("FINANCE") == 100
    assert foundation_floor("  Cfo  ") == 100


def test_the_da1_regression_finance_at_70_must_reframe() -> None:
    """The exact bug: 70 in a finance domain used to PASS. It must REFRAME."""
    assert foundation_verdict(_attack(70), "finance") == Verdict.REFRAME
    assert foundation_verdict(_attack(99), "finance") == Verdict.REFRAME
    assert foundation_verdict(_attack(100), "finance") == Verdict.PASS


def test_blockchain_floor_is_enforced() -> None:
    assert foundation_verdict(_attack(84), "defi") == Verdict.REFRAME
    assert foundation_verdict(_attack(85), "defi") == Verdict.PASS


def test_general_domain_keeps_the_default_behaviour() -> None:
    assert foundation_verdict(_attack(70), "general") == Verdict.PASS
    assert foundation_verdict(_attack(69), "general") == Verdict.REFRAME


def test_default_argument_is_general_so_old_callers_are_unchanged() -> None:
    assert foundation_verdict(_attack(70)) == Verdict.PASS


def test_near_miss_domain_warns_rather_than_silently_downgrading(caplog) -> None:
    with caplog.at_level(logging.WARNING, logger="chp.foundation"):
        assert foundation_floor("finance_adversary") == DEFAULT_FOUNDATION_FLOOR
    assert any("resembles" in r.getMessage() for r in caplog.records)


def test_engine_floors_match_the_conformance_reference() -> None:
    """Engine and spec reference must not drift — that drift was D-A1."""
    import importlib.util
    from pathlib import Path

    # walk up to the repo root so this works wherever the tests live
    ref_path = None
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "spec" / "conformance" / "chp_reference.py"
        if candidate.exists():
            ref_path = candidate
            break
    assert ref_path is not None, "spec/conformance/chp_reference.py not found"
    import sys

    spec = importlib.util.spec_from_file_location("chp_reference", ref_path)
    ref = importlib.util.module_from_spec(spec)
    sys.modules["chp_reference"] = ref  # dataclasses resolves InitVar via sys.modules
    spec.loader.exec_module(ref)
    assert dict(FOUNDATION_FLOORS) == dict(ref.FOUNDATION_FLOORS)
    assert DEFAULT_FOUNDATION_FLOOR == ref.DEFAULT_FOUNDATION_FLOOR
