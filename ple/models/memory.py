"""Memory object models — see memory_contract.md and TYPES.md."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field

from ple.errors import ContractViolation

RESOLUTION_STATES = frozenset({"unresolved", "partial", "collapsed"})


@dataclass(frozen=True)
class TensionSignature:
    """Compressed representation of tension topology (memory_contract.md §4)."""

    paradox_density: float
    tension_distribution: dict = field(default_factory=dict)
    coherence_profile: dict = field(default_factory=dict)
    void_ratio: float = 0.0
    signature_id: str = field(default_factory=lambda: f"ts-{uuid.uuid4().hex[:12]}")


@dataclass(frozen=True)
class ParadoxMemoryEpisode:
    """The atomic unit of PLE memory: one full
    paradox -> tension -> lattice -> synthesis -> attractor -> finding cycle.
    """

    paradox_ids: tuple[str, ...]
    tension_signature: TensionSignature
    lattice_snapshot_id: str
    synthesis_ids: tuple[str, ...]
    attractor_ids: tuple[str, ...] = ()
    finding_ids: tuple[str, ...] = ()
    resolution_state: str = "unresolved"
    identity_shift_delta: dict = field(default_factory=dict)
    context_window: dict = field(default_factory=dict)
    lineage: tuple[str, ...] = ()
    timestamp: float = field(default_factory=time.time)
    episode_id: str = field(default_factory=lambda: f"ep-{uuid.uuid4().hex[:12]}")

    def __post_init__(self) -> None:
        if not self.paradox_ids:
            raise ContractViolation("an episode requires at least one paradox")
        if self.resolution_state not in RESOLUTION_STATES:
            raise ContractViolation(
                f"invalid resolution_state {self.resolution_state!r}"
            )
