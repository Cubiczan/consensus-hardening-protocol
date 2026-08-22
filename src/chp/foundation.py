"""Foundation-stage helpers for CHP.

The foundation gate compares an adversary's ``foundation_score`` against a
**domain-dependent** floor (spec §5.3). Earlier ports hardcoded 70 for every
domain, so a finance decision scoring 70 cleared a gate documented as requiring
100 — divergence D-A1, the highest-severity finding in ``spec/DIVERGENCES.md``.
The floor map below is the normative behaviour and matches
``spec/conformance/chp_reference.py`` exactly, so the engine and the conformance
suite cannot drift apart.
"""
from __future__ import annotations

import logging
from typing import Mapping

from chp.models import FoundationAttack, FoundationDisclosure, Verdict

logger = logging.getLogger(__name__)

#: Domain foundation-score floors (spec §5.3). A domain absent from this map
#: uses DEFAULT_FOUNDATION_FLOOR — failing to the default, never to 0.
FOUNDATION_FLOORS: Mapping[str, int] = {
    "general": 70,
    "ai": 70,
    "agents": 70,
    "blockchain": 85,
    "defi": 85,
    "finance": 100,
    "cfo": 100,
    "capital_allocation": 100,
    "board_decision": 100,
}
DEFAULT_FOUNDATION_FLOOR = 70


def foundation_floor(domain: str | None) -> int:
    """Resolve the foundation-score floor for a domain (spec §5.3).

    Case-insensitive, exact match. Unknown domains fall back to the general
    floor rather than failing open at 0 or closed at 100.

    A domain that merely *resembles* a listed one — ``finance_adversary`` against
    ``finance`` — is still unlisted and still gets the default floor, because the
    spec mandates exact matching. That is quiet enough to reintroduce D-A1 by
    naming alone, so it is logged at WARNING.
    """
    key = (domain or "").strip().lower()
    if key in FOUNDATION_FLOORS:
        return FOUNDATION_FLOORS[key]
    for known, floor in FOUNDATION_FLOORS.items():
        if floor > DEFAULT_FOUNDATION_FLOOR and key.startswith(known):
            logger.warning(
                "domain %r is unlisted so it gates at the default floor %d, but it "
                "resembles %r which requires %d — rename it or add it to "
                "FOUNDATION_FLOORS if the stricter floor was intended",
                domain, DEFAULT_FOUNDATION_FLOOR, known, floor,
            )
            break
    return DEFAULT_FOUNDATION_FLOOR


def foundation_verdict(attack: FoundationAttack, domain: str = "general") -> Verdict:
    """Gate a foundation attack against its domain floor (spec §5.3)."""
    return Verdict.PASS if attack.foundation_score >= foundation_floor(domain) else Verdict.REFRAME


def validate_foundation_pair(
    disclosure: FoundationDisclosure, attack: FoundationAttack
) -> list[str]:
    errors = disclosure.validate() + attack.validate()
    if disclosure.weakest_assumptions and attack.assumption_attacks:
        if len(attack.assumption_attacks) < min(3, len(disclosure.weakest_assumptions)):
            errors.append("attack must address each disclosed weak assumption")
    return errors
