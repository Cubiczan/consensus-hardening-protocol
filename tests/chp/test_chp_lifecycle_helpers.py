"""Registry lookups, high-stakes domains, provisional-lock advance, accuracy guard."""
import pytest

from chp import (
    CHPOrchestrator,
    DecisionCase,
    Dossier,
    FoundationAttack,
    FoundationDisclosure,
    SessionStatus,
)
from chp.accuracy import AccuracyGuardResult, run_accuracy_guard
from chp.registry import DecisionRegistry


def _case(decision_id="d-1", domain="general", status=SessionStatus.EXPLORING, **kw):
    case = DecisionCase(
        decision_id=decision_id,
        title=decision_id,
        domain=domain,
        created_at="2026-10-06T00:00:00Z",
        owner="t",
        high_stakes=kw.pop("high_stakes", False),
        dossier=Dossier(
            core_problem="p", scope="s", current_state="c", prior_decisions=[], constraints=[]
        ) if kw.pop("with_dossier", False) else None,
    )
    case.status = status
    for k, v in kw.items():
        setattr(case, k, v)
    return case


def test_registry_lookups():
    reg = DecisionRegistry()
    reg.add(_case("a", "finance", SessionStatus.LOCKED))
    reg.add(_case("b", "Finance"))
    reg.add(_case("c", "ops"))
    assert reg.count() == 3
    assert {c.decision_id for c in reg.find_by_domain("FINANCE")} == {"a", "b"}
    assert [c.decision_id for c in reg.find_by_status(SessionStatus.LOCKED)] == ["a"]
    assert reg.remove("c") is True
    assert reg.remove("c") is False
    assert reg.count() == 2


def test_advance_to_provisional_lock_guards():
    orch = CHPOrchestrator()
    orch.registry.add(_case("ok"))
    orch.registry.add(_case("halted", status=SessionStatus.HALT))
    orch.registry.add(_case("reframe", status=SessionStatus.REFRAME_REQUIRED))
    assert orch.advance_to_provisional_lock("ok").status == SessionStatus.PROVISIONAL_LOCK
    with pytest.raises(ValueError, match="halted"):
        orch.advance_to_provisional_lock("halted")
    with pytest.raises(ValueError, match="reframing"):
        orch.advance_to_provisional_lock("reframe")
    with pytest.raises(KeyError):
        orch.advance_to_provisional_lock("missing")


def test_custom_high_stakes_domains_drive_r0_worth_it():
    assert CHPOrchestrator().high_stakes_domains == {"capital_allocation", "board_decision"}
    custom = CHPOrchestrator(high_stakes_domains={"synergy_tracking"})
    assert "synergy_tracking" in custom.high_stakes_domains
    assert "board_decision" not in custom.high_stakes_domains


def test_accuracy_guard():
    clear = _case(foundation_score=100)
    r = run_accuracy_guard(clear)
    assert isinstance(r, AccuracyGuardResult) and r.passes and r.required_action == "PROCEED"

    low = run_accuracy_guard(_case(foundation_score=85))
    assert not low.passes and low.required_action == "REQUIRES_HUMAN_VERIFICATION"
    assert "below" in low.reason

    assert run_accuracy_guard(_case(foundation_score=70), floor=70).passes

    vuln = run_accuracy_guard(_case(foundation_score=100, structural_vulnerabilities=["x"]))
    assert not vuln.passes
