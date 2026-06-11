"""Paradox ecology metrics — density, tension load, synthesis quality,
stability profiles (ARCHITECTURE.md §6.6).
"""

from __future__ import annotations

from ple.models.lattice import ParadoxLattice
from ple.models.synthesis import SynthesisRecord
from ple.models.tension_field import TensionField


def paradox_density(lattice: ParadoxLattice) -> float:
    """How paradox-rich is the lattice right now?"""
    nodes = lattice.nodes
    if not nodes:
        return 0.0
    return len(lattice.nodes_of_type("paradox")) / len(nodes)


def tension_load(field: TensionField) -> float:
    """Global tension currently carried by the field."""
    return field.global_intensity


def synthesis_quality(records: list[SynthesisRecord]) -> float:
    if not records:
        return 0.0
    return sum(r.quality_score for r in records) / len(records)


def stability_profile(lattice: ParadoxLattice) -> dict:
    nodes = lattice.nodes
    return {
        "node_stability": {n.node_id: n.stability_score for n in nodes},
        "global_stability": (
            sum(n.stability_score for n in nodes) / len(nodes) if nodes else 0.0
        ),
    }
