"""Lattice pattern store — recurring structural motifs in the lattice
(Phase 2: lattice pattern store; memory_contract.md: memory may cluster
patterns but must not alter originals).

A pattern is a topological signature of a lattice snapshot: how many nodes
of each type, how many edges of each relation, and which
paradox->synthesis->attractor motifs are present. Recurring signatures
across episodes reveal the lattice settling into characteristic shapes —
the raw material for recognizing "we have structured tension like this
before."
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
import uuid


@dataclass(frozen=True)
class LatticePattern:
    signature: tuple
    snapshot_ids: tuple[str, ...]
    pattern_id: str = field(default_factory=lambda: f"lp-{uuid.uuid4().hex[:12]}")

    @property
    def recurrence(self) -> int:
        return len(self.snapshot_ids)


def _bucket(count: int) -> int:
    """Logarithmic size bucket (1, 2-3, 4-7, 8-15, ...). The lattice grows
    monotonically — synthesis history accumulates — so raw counts never
    repeat. Bucketing makes the signature scale-coarse: a settled ecology's
    *shape* recurs even while it slowly grows."""
    return count.bit_length()


def signature_of(snapshot: dict) -> tuple:
    """Topological signature: bucketed node-type census, bucketed
    edge-relation census, and the exact count of complete
    paradox->synthesis->attractor chains."""
    node_census = Counter(n["node_type"] for n in snapshot["nodes"])
    edge_census = Counter(e["relation_type"] for e in snapshot["edges"])

    by_id = {n["node_id"]: n for n in snapshot["nodes"]}
    synth_to_attractor = {
        e["source"]
        for e in snapshot["edges"]
        if e["relation_type"] == "attractor_link"
        and by_id.get(e["source"], {}).get("node_type") == "synthesis"
    }
    chains = sum(
        1
        for e in snapshot["edges"]
        if e["relation_type"] == "synthesis"
        and by_id.get(e["source"], {}).get("node_type") == "paradox"
        and e["target"] in synth_to_attractor
    )

    return (
        tuple(sorted((t, _bucket(c)) for t, c in node_census.items())),
        tuple(sorted((t, _bucket(c)) for t, c in edge_census.items())),
        ("paradox_synthesis_attractor_chains", chains),
    )


class LatticePatternStore:
    """Append-only: snapshots are clustered by signature, never altered."""

    def __init__(self) -> None:
        self._clusters: dict[tuple, list[str]] = defaultdict(list)

    def record(self, snapshot: dict) -> tuple:
        sig = signature_of(snapshot)
        self._clusters[sig].append(snapshot["snapshot_id"])
        return sig

    def patterns(self, min_recurrence: int = 1) -> list[LatticePattern]:
        return [
            LatticePattern(signature=sig, snapshot_ids=tuple(ids))
            for sig, ids in self._clusters.items()
            if len(ids) >= min_recurrence
        ]

    def recurrence_of(self, snapshot: dict) -> int:
        """How many times has this snapshot's shape been seen?"""
        return len(self._clusters[signature_of(snapshot)])
