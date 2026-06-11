"""Stage 1c — paradox intensity estimation and the sole authorized
intensity mutator (paradox_contract.md §4: "No other module may mutate
intensity").
"""

from __future__ import annotations

from ple.models._mutation import authorized_set
from ple.models.paradox import ParadoxNode
from ple.paradox.paradox_detector import RawContradiction

ACTOR = "paradox_intensity_model"

# Sharper contradiction kinds run hotter.
_TYPE_HEAT = {
    "logical": 0.9,
    "self_referential": 0.8,
    "semantic": 0.6,
    "contextual": 0.4,
}


def estimate(
    contradiction: RawContradiction,
    contradiction_type: str,
    context: dict | None = None,
) -> float:
    """Estimate paradox intensity in [0,1] — tension magnitude, not importance."""
    context = context or contradiction.context
    base = _TYPE_HEAT.get(contradiction_type, 0.5)
    # Evidence on both sides sharpens the contradiction (bidirectional tension).
    evidence_weight = min(
        len(context.get("supporting_evidence", [])),
        len(context.get("opposing_evidence", [])),
    )
    heat = base + 0.05 * evidence_weight
    return max(0.01, min(1.0, heat))


def update_intensity(node: ParadoxNode, new_intensity: float) -> None:
    """Adjust a paradox's intensity. Clamped to [0,1] per contract."""
    authorized_set(
        node, "intensity", max(0.0, min(1.0, new_intensity)), actor=ACTOR
    )


def attenuate(node: ParadoxNode, tension_reduction: float) -> None:
    """Reduce intensity when synthesis reduces tension (called on behalf of
    the synthesis layer, which may not touch intensity itself)."""
    update_intensity(node, node.intensity * (1.0 - tension_reduction))


def intensify(node: ParadoxNode, delta: float) -> None:
    """Increase intensity when contradictions sharpen."""
    update_intensity(node, node.intensity + abs(delta))
