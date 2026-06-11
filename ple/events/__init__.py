"""Typed events for cross-layer communication — see ARCHITECTURE.md §7.

Each event class declares its valid event types per its contract; the
contracts also forbid certain types globally (paradoxes are never 'resolved'
or 'deleted', etc.). Construction validates against both.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import ClassVar

from ple.errors import InvalidEvent

# Globally forbidden across all contracts.
FORBIDDEN_EVENT_TYPES = frozenset({"resolved", "deleted", "collapsed_paradox", "overwritten"})


@dataclass(frozen=True)
class _BaseEvent:
    VALID_TYPES: ClassVar[frozenset[str]] = frozenset()

    event_type: str = ""
    metadata: dict = field(default_factory=dict)
    event_id: str = field(default_factory=lambda: f"ev-{uuid.uuid4().hex[:12]}")

    def __post_init__(self) -> None:
        if self.event_type in FORBIDDEN_EVENT_TYPES:
            raise InvalidEvent(
                f"event type {self.event_type!r} is forbidden by the PLE contracts"
            )
        if self.event_type not in self.VALID_TYPES:
            raise InvalidEvent(
                f"{type(self).__name__} does not allow event type "
                f"{self.event_type!r}; valid: {sorted(self.VALID_TYPES)}"
            )


@dataclass(frozen=True)
class ParadoxEvent(_BaseEvent):
    VALID_TYPES: ClassVar[frozenset[str]] = frozenset(
        {"detected", "normalized", "updated", "nested", "attenuated", "archived"}
    )
    paradox_id: str = ""


@dataclass(frozen=True)
class TensionFieldEvent(_BaseEvent):
    VALID_TYPES: ClassVar[frozenset[str]] = frozenset(
        {"generated", "expanded", "collapsed", "intensified", "diffused", "updated", "archived"}
    )
    field_id: str = ""


@dataclass(frozen=True)
class LatticeUpdateEvent(_BaseEvent):
    VALID_TYPES: ClassVar[frozenset[str]] = frozenset(
        {"node_added", "edge_added", "simplified", "expanded", "stabilized", "reweighted", "archived"}
    )
    lattice_id: str = ""


@dataclass(frozen=True)
class SynthesisEvent(_BaseEvent):
    VALID_TYPES: ClassVar[frozenset[str]] = frozenset(
        {"created", "evaluated", "updated", "promoted_to_attractor_candidate", "deprecated"}
    )
    synthesis_id: str = ""


@dataclass(frozen=True)
class ResolutionEvent(_BaseEvent):
    VALID_TYPES: ClassVar[frozenset[str]] = frozenset(
        {"collapsed", "stabilized", "deferred"}
    )
    horizon_id: str = ""


@dataclass(frozen=True)
class AttractorEvent(_BaseEvent):
    VALID_TYPES: ClassVar[frozenset[str]] = frozenset(
        {"candidate_created", "forming", "activated", "stabilized", "attenuated", "archived"}
    )
    attractor_id: str = ""


@dataclass(frozen=True)
class FindingEvent(_BaseEvent):
    VALID_TYPES: ClassVar[frozenset[str]] = frozenset(
        {"finding_created", "finding_validated", "finding_deprecated", "finding_exported"}
    )
    finding_id: str = ""


@dataclass(frozen=True)
class MemoryEvent(_BaseEvent):
    VALID_TYPES: ClassVar[frozenset[str]] = frozenset(
        {
            "episode_created",
            "snapshot_created",
            "signature_compressed",
            "finding_recorded",
            "attractor_archived",
            "episode_archived",
        }
    )
    object_id: str = ""


__all__ = [
    "AttractorEvent",
    "FindingEvent",
    "FORBIDDEN_EVENT_TYPES",
    "LatticeUpdateEvent",
    "MemoryEvent",
    "ParadoxEvent",
    "ResolutionEvent",
    "SynthesisEvent",
    "TensionFieldEvent",
]
