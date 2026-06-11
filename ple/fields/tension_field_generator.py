"""Stage 2 — tension field generation.

Builds a TensionField from the active paradox set: paradoxes cluster into
regions by contradiction type (a proxy for tension topology), gradients point
toward denser neighboring regions, and the coherence map scores each frame by
how much paradox heat it participates in.
"""

from __future__ import annotations

from collections import defaultdict

from ple.models.paradox import ParadoxNode
from ple.models.tension_field import FieldState, TensionField, TensionRegion

ACTOR = "tension_field_generator"


def build(active_paradoxes: list[ParadoxNode], context: dict | None = None) -> TensionField:
    context = context or {}
    if not active_paradoxes:
        raise ValueError("cannot build a tension field with no active paradoxes")

    clusters: dict[str, list[ParadoxNode]] = defaultdict(list)
    for node in active_paradoxes:
        clusters[node.contradiction_type].append(node)

    # First pass: density per cluster so gradients can point uphill.
    densities = {
        ctype: sum(n.intensity for n in nodes) / len(nodes)
        for ctype, nodes in clusters.items()
    }
    region_ids = {ctype: f"rg-{ctype}" for ctype in clusters}

    regions: list[TensionRegion] = []
    for ctype, nodes in sorted(clusters.items()):
        density = densities[ctype]
        neighbors = tuple(
            region_ids[other] for other in sorted(clusters) if other != ctype
        )
        # Directional tension flow: positive toward denser neighbors.
        gradient = {
            region_ids[other]: round(densities[other] - density, 6)
            for other in sorted(clusters)
            if other != ctype
        }
        regions.append(
            TensionRegion(
                region_id=region_ids[ctype],
                paradox_ids=tuple(n.paradox_id for n in nodes),
                tension_density=max(density, 1e-9),
                coherence_score=max(0.0, 1.0 - density),
                gradient_vector=gradient,
                neighbors=neighbors,
            )
        )

    field = TensionField(
        regions=tuple(regions),
        global_intensity=sum(n.intensity for n in active_paradoxes)
        / len(active_paradoxes),
        coherence_map=compute_coherence(active_paradoxes),
        void_zones=tuple(context.get("void_zones", ())),
    )
    field.transition(FieldState.ACTIVE, actor=ACTOR)
    return field


def compute_coherence(paradoxes: list[ParadoxNode]) -> dict[str, float]:
    """Frame coherence decreases as the paradox intensity it participates in
    increases (field_contract.md §4)."""
    heat: dict[str, list[float]] = defaultdict(list)
    for node in paradoxes:
        heat[node.frame_a].append(node.intensity)
        heat[node.frame_b].append(node.intensity)
    return {
        frame: round(max(0.0, 1.0 - sum(vals) / len(vals)), 6)
        for frame, vals in heat.items()
    }
