"""SynthesisRecord model — see synthesis_contract.md."""

from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass, field

from ple.errors import ContractViolation, InvalidLifecycleTransition
from ple.models._mutation import authorized_set

SYNTHESIS_METHODS = frozenset({"coexistence", "hybridization", "reframing"})


class SynthesisState(str, enum.Enum):
    CREATED = "created"
    EVALUATED = "evaluated"
    PROMOTED_TO_CANDIDATE = "promoted_to_candidate"
    DEPRECATED = "deprecated"


_TRANSITIONS: dict[tuple[SynthesisState, SynthesisState], frozenset[str]] = {
    (SynthesisState.CREATED, SynthesisState.EVALUATED): frozenset(
        {"synthesis_engine"}
    ),
    (SynthesisState.EVALUATED, SynthesisState.PROMOTED_TO_CANDIDATE): frozenset(
        {"attractor_detector"}
    ),
    (SynthesisState.EVALUATED, SynthesisState.DEPRECATED): frozenset(
        {"synthesis_engine"}
    ),
    (SynthesisState.PROMOTED_TO_CANDIDATE, SynthesisState.DEPRECATED): frozenset(
        {"synthesis_engine"}
    ),
}


@dataclass(frozen=True)
class SynthesisRecord:
    """A new cognitive structure generated from tension.

    Immutable once created (synthesis_contract.md §2); only the lifecycle
    state advances, via the authorized actors.
    """

    paradox_ids: tuple[str, ...]
    method: str
    resulting_frame: str
    quality_score: float
    tension_reduction: float
    lineage: tuple[str, ...] = ()
    synthesis_id: str = field(default_factory=lambda: f"sy-{uuid.uuid4().hex[:12]}")
    state: SynthesisState = SynthesisState.CREATED

    def __post_init__(self) -> None:
        if not self.paradox_ids:
            raise ContractViolation("synthesis paradox_ids must be non-empty")
        if self.method not in SYNTHESIS_METHODS:
            raise ContractViolation(
                f"invalid synthesis method {self.method!r}; allowed: "
                f"{sorted(SYNTHESIS_METHODS)} (no other method may be introduced "
                "without updating synthesis_contract.md)"
            )
        if not (0.0 <= self.tension_reduction <= 1.0):
            raise ContractViolation("tension_reduction must be within [0.0, 1.0]")
        if not (0.0 <= self.quality_score <= 1.0):
            raise ContractViolation("quality_score must be within [0.0, 1.0]")
        if not self.resulting_frame.strip():
            raise ContractViolation("resulting_frame must be a coherent frame")

    def transition(self, new_state: SynthesisState, *, actor: str) -> None:
        key = (self.state, new_state)
        allowed = _TRANSITIONS.get(key)
        if allowed is None:
            raise InvalidLifecycleTransition(
                f"synthesis transition {self.state.value} -> {new_state.value} "
                "is not permitted"
            )
        if actor not in allowed:
            raise InvalidLifecycleTransition(
                f"actor '{actor}' may not perform synthesis transition "
                f"{self.state.value} -> {new_state.value}"
            )
        authorized_set(self, "state", new_state, actor=actor)
