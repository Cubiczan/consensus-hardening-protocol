"""Consensus Hardening Protocol primitives.

CHP is the decision-governance layer for high-stakes, cross-model finance
workflows. This package provides the canonical data model, gate logic,
payload-integrity helpers, and an in-memory registry that higher-level finance
workflows can build on.
"""

from chp.models import (
    ContextCheck,
    DecisionCase,
    DevilsAdvocateRound,
    Dossier,
    FoundationAttack,
    FoundationDisclosure,
    ModelParityCheck,
    ModelTier,
    Phase,
    RoundRecord,
    SessionStatus,
    StateSnapshot,
    ThirdPartyValidation,
    VCLDiagnosis,
    ValidationResult,
    Verdict,
)
from chp.parity import assess_model_parity
from chp.payloads import (
    PayloadEnvelope,
    build_payload_envelope,
    extract_payload_id,
    payload_echo_confirmed,
    validate_payload_envelope,
)
from chp.accuracy import CFOAccuracyPolicy, FinancialAnalysisGuard, FinancialAnalysisGuardResult
from chp.contracts import (
    ConvergenceClosure,
    CouncilSpawn,
    InterruptionRecovery,
    ItemAgreement,
    OriginPacketContract,
    PartnerPacket,
    ScoringOption,
    VerificationChecklist,
)
from chp.gates import evaluate_phase_gate, evaluate_r0_gate
from chp.orchestrator import CHPOrchestrator, CHPReport
from chp.registry import DecisionRegistry
from chp.runner import TriangulationResult, TriangulationRunner
from chp.validators import apply_third_party_validation

__all__ = [
    "AdversaryMeshAgent",
    "CFOAccuracyPolicy",
    "ContextCheck",
    "ConvergenceClosure",
    "CouncilSpawn",
    "DecisionCase",
    "DecisionRegistry",
    "DevilsAdvocateRound",
    "Dossier",
    "FinancialAnalysisGuard",
    "FinancialAnalysisGuardResult",
    "FoundationAttack",
    "FoundationDisclosure",
    "CHPOrchestrator",
    "CHPReport",
    "InterruptionRecovery",
    "ItemAgreement",
    "ModelParityCheck",
    "ModelTier",
    "OriginPacketContract",
    "PartnerPacket",
    "Phase",
    "PayloadEnvelope",
    "RoundRecord",
    "ScoringOption",
    "SessionStatus",
    "StateSnapshot",
    "ThirdPartyValidation",
    "TriangulationResult",
    "TriangulationRunner",
    "VCLDiagnosis",
    "ValidationResult",
    "VerificationChecklist",
    "Verdict",
    "apply_third_party_validation",
    "assess_model_parity",
    "build_payload_envelope",
    "evaluate_phase_gate",
    "evaluate_r0_gate",
    "extract_payload_id",
    "payload_echo_confirmed",
    "validate_payload_envelope",
]


def __getattr__(name: str):
    """Expose the optional mesh adapter without importing its dependency eagerly.

    ``AdversaryMeshAgent`` subclasses ``cme.agent.MeshAgent``, which ships with
    the Cognitive Mesh host rather than this package. Importing it here would
    make the whole package unimportable without that host.
    """
    if name == "AdversaryMeshAgent":
        from chp.adapters.adversary_agent import AdversaryMeshAgent

        return AdversaryMeshAgent
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

