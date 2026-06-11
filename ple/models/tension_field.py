"""TensionField and TensionRegion models — see field_contract.md and TYPES.md."""

from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass, field

from ple.errors import ContractViolation, InvalidLifecycleTransition
from ple.models._mutation import authorized_set


class FieldState(str, enum.Enum):
    GENERATED = "generated"
    ACTIVE = "active"
    EXPANDED = "expanded"
    COLLAPSED = "collapsed"
    ARCHIVED = "archived"


_TRANSITIONS: dict[tuple[FieldState, FieldState], frozenset[str]] = {
    (FieldState.GENERATED, FieldState.ACTIVE): frozenset(
        {"tension_field_generator"}
    ),
    (FieldState.ACTIVE, FieldState.EXPANDED): frozenset(
        {"tension_field_generator"}
    ),
    (FieldState.ACTIVE, FieldState.COLLAPSED): frozenset(
        {"synthesis_engine", "attractor_evolution"}
    ),
    (FieldState.EXPANDED, FieldState.COLLAPSED): frozenset(
        {"synthesis_engine", "attractor_evolution"}
    ),
    (FieldState.ACTIVE, FieldState.ARCHIVED): frozenset({"memory"}),
    (FieldState.EXPANDED, FieldState.ARCHIVED): frozenset({"memory"}),
    (FieldState.COLLAPSED, FieldState.ARCHIVED): frozenset({"memory"}),
}


@dataclass(frozen=True)
class TensionRegion:
    """Atomic unit of a TensionField (field_contract.md §3)."""

    paradox_ids: tuple[str, ...]
    tension_density: float
    coherence_score: float
    gradient_vector: dict = field(default_factory=dict)
    neighbors: tuple[str, ...] = ()
    region_id: str = field(default_factory=lambda: f"rg-{uuid.uuid4().hex[:12]}")

    def __post_init__(self) -> None:
        if not self.paradox_ids:
            raise ContractViolation("a tension region requires at least one paradox")
        if self.tension_density <= 0.0:
            raise ContractViolation("region tension density must be non-zero positive")
        if self.region_id in self.neighbors:
            raise ContractViolation("a region may not be its own neighbor")


@dataclass(frozen=True)
class TensionField:
    """Geometric representation of paradox-induced tension.

    Mutable only through approved processors (tension_field_generator,
    tension_topology, coherence_map) — see field_contract.md §6.
    """

    regions: tuple[TensionRegion, ...]
    global_intensity: float
    coherence_map: dict = field(default_factory=dict)
    void_zones: tuple[str, ...] = ()
    field_id: str = field(default_factory=lambda: f"tf-{uuid.uuid4().hex[:12]}")
    state: FieldState = FieldState.GENERATED

    def __post_init__(self) -> None:
        if not self.regions:
            raise ContractViolation("a tension field must contain regions")
        if self.global_intensity < 0.0:
            raise ContractViolation("tension cannot be negative")
        for score in self.coherence_map.values():
            if not (0.0 <= score <= 1.0):
                raise ContractViolation("coherence scores must be within [0.0, 1.0]")
        region_ids = {r.region_id for r in self.regions}
        for r in self.regions:
            for n in r.neighbors:
                if n not in region_ids:
                    raise ContractViolation(
                        f"region {r.region_id} names unknown neighbor {n}"
                    )

    def transition(self, new_state: FieldState, *, actor: str) -> None:
        key = (self.state, new_state)
        allowed = _TRANSITIONS.get(key)
        if allowed is None:
            raise InvalidLifecycleTransition(
                f"field transition {self.state.value} -> {new_state.value} "
                "is not permitted"
            )
        if actor not in allowed:
            raise InvalidLifecycleTransition(
                f"actor '{actor}' may not perform field transition "
                f"{self.state.value} -> {new_state.value}"
            )
        authorized_set(self, "state", new_state, actor=actor)

    @property
    def paradox_ids(self) -> frozenset[str]:
        return frozenset(pid for r in self.regions for pid in r.paradox_ids)
