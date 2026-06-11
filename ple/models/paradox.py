"""ParadoxNode model — see paradox_contract.md and TYPES.md."""

from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass, field

from ple.errors import InvalidLifecycleTransition, InvalidParadox
from ple.models._mutation import authorized_set

CONTRADICTION_TYPES = frozenset(
    {"logical", "semantic", "contextual", "self_referential"}
)


class ParadoxState(str, enum.Enum):
    DETECTED = "detected"
    NORMALIZED = "normalized"
    ACTIVE = "active"
    ATTENUATED = "attenuated"
    ARCHIVED = "archived"


# transition -> set of actors permitted to perform it (paradox_contract.md §5)
_TRANSITIONS: dict[tuple[ParadoxState, ParadoxState], frozenset[str]] = {
    (ParadoxState.DETECTED, ParadoxState.NORMALIZED): frozenset({"paradox_layer"}),
    (ParadoxState.NORMALIZED, ParadoxState.ACTIVE): frozenset({"paradox_layer"}),
    (ParadoxState.ACTIVE, ParadoxState.ATTENUATED): frozenset(
        {"synthesis_engine", "attractor_evolution"}
    ),
    (ParadoxState.ACTIVE, ParadoxState.ARCHIVED): frozenset({"memory"}),
    (ParadoxState.ATTENUATED, ParadoxState.ARCHIVED): frozenset({"memory"}),
    # Re-intensification can reactivate an attenuated paradox.
    (ParadoxState.ATTENUATED, ParadoxState.ACTIVE): frozenset({"paradox_layer"}),
}


@dataclass(frozen=True)
class ParadoxNode:
    """A structured contradiction between incompatible frames.

    Immutable except for intensity (paradox_intensity_model only), lineage
    (append-only), nested_paradox_ids (paradox_normalizer only), and
    lifecycle state transitions by the authorized layers.
    """

    frame_a: str
    frame_b: str
    contradiction_type: str
    intensity: float
    context_window: dict = field(default_factory=dict)
    supporting_evidence: tuple[str, ...] = ()
    opposing_evidence: tuple[str, ...] = ()
    lineage: tuple[str, ...] = ()
    nested_paradox_ids: tuple[str, ...] = ()
    paradox_id: str = field(default_factory=lambda: f"px-{uuid.uuid4().hex[:12]}")
    state: ParadoxState = ParadoxState.DETECTED

    def __post_init__(self) -> None:
        if self.contradiction_type not in CONTRADICTION_TYPES:
            raise InvalidParadox(
                f"unknown contradiction_type {self.contradiction_type!r}; "
                f"must be one of {sorted(CONTRADICTION_TYPES)}"
            )
        if not (0.0 <= self.intensity <= 1.0):
            raise InvalidParadox("intensity must be within [0.0, 1.0]")
        if self.frame_a == self.frame_b:
            raise InvalidParadox(
                "frame incompatibility requires two distinct frames"
            )

    def transition(self, new_state: ParadoxState, *, actor: str) -> None:
        key = (self.state, new_state)
        allowed = _TRANSITIONS.get(key)
        if allowed is None:
            raise InvalidLifecycleTransition(
                f"paradox transition {self.state.value} -> {new_state.value} "
                "is not permitted"
            )
        if actor not in allowed:
            raise InvalidLifecycleTransition(
                f"actor '{actor}' may not perform paradox transition "
                f"{self.state.value} -> {new_state.value}; "
                f"authorized: {sorted(allowed)}"
            )
        authorized_set(self, "state", new_state, actor=actor)

    @property
    def is_valid(self) -> bool:
        """Validity conditions from paradox_contract.md §6."""
        return (
            self.intensity > 0.0
            and self.frame_a != self.frame_b
            and self.contradiction_type in CONTRADICTION_TYPES
        )

    @property
    def frames(self) -> frozenset[str]:
        return frozenset({self.frame_a, self.frame_b})
