"""Attractor model — see attractor_contract.md."""

from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass, field

from ple.errors import ContractViolation, InvalidLifecycleTransition
from ple.models._mutation import authorized_set

ATTRACTOR_TYPES = frozenset({"coexistence", "hybrid", "reframed", "emergent"})


class AttractorState(str, enum.Enum):
    CANDIDATE = "candidate"
    FORMING = "forming"
    ACTIVE = "active"
    STABILIZING = "stabilizing"
    ATTENUATED = "attenuated"
    ARCHIVED = "archived"


# attractor_contract.md §6: each promotion has exactly one authorized module.
_TRANSITIONS: dict[tuple[AttractorState, AttractorState], frozenset[str]] = {
    (AttractorState.CANDIDATE, AttractorState.FORMING): frozenset(
        {"attractor_detector"}
    ),
    (AttractorState.FORMING, AttractorState.ACTIVE): frozenset(
        {"attractor_evolution"}
    ),
    (AttractorState.ACTIVE, AttractorState.STABILIZING): frozenset(
        {"attractor_stability"}
    ),
    (AttractorState.ACTIVE, AttractorState.ATTENUATED): frozenset(
        {"attractor_stability"}
    ),
    (AttractorState.STABILIZING, AttractorState.ATTENUATED): frozenset(
        {"attractor_stability"}
    ),
    (AttractorState.STABILIZING, AttractorState.ARCHIVED): frozenset({"memory"}),
    (AttractorState.ACTIVE, AttractorState.ARCHIVED): frozenset({"memory"}),
    (AttractorState.ATTENUATED, AttractorState.ARCHIVED): frozenset({"memory"}),
}


@dataclass(frozen=True)
class Attractor:
    """A stable cognitive structure emerging from repeated syntheses.

    Immutable except for stability_score (attractor_stability only),
    basin expansion and lineage extension (attractor_evolution only).
    """

    type: str
    core_syntheses: tuple[str, ...]
    stability_score: float
    tension_profile: dict = field(default_factory=dict)
    basin_nodes: tuple[str, ...] = ()
    lineage: tuple[str, ...] = ()
    attractor_id: str = field(default_factory=lambda: f"at-{uuid.uuid4().hex[:12]}")
    state: AttractorState = AttractorState.CANDIDATE

    def __post_init__(self) -> None:
        if self.type not in ATTRACTOR_TYPES:
            raise ContractViolation(
                f"invalid attractor type {self.type!r}; allowed: "
                f"{sorted(ATTRACTOR_TYPES)} (no new types without updating "
                "attractor_contract.md)"
            )
        if not self.core_syntheses:
            raise ContractViolation("core_syntheses must be non-empty")
        if not (0.0 <= self.stability_score <= 1.0):
            raise ContractViolation("stability_score must be within [0.0, 1.0]")

    def transition(self, new_state: AttractorState, *, actor: str) -> None:
        key = (self.state, new_state)
        allowed = _TRANSITIONS.get(key)
        if allowed is None:
            raise InvalidLifecycleTransition(
                f"attractor transition {self.state.value} -> {new_state.value} "
                "is not permitted"
            )
        if actor not in allowed:
            raise InvalidLifecycleTransition(
                f"actor '{actor}' may not perform attractor transition "
                f"{self.state.value} -> {new_state.value}; "
                f"authorized: {sorted(allowed)}"
            )
        authorized_set(self, "state", new_state, actor=actor)
