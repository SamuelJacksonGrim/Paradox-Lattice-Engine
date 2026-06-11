"""Finding extraction — triggered by attractor dynamics.

Findings may only be generated from stable attractors with converged basins
and complete lineage (finding_contract.md §3) — never from single syntheses
or transient lattice states.
"""

from __future__ import annotations

from ple.errors import ContractViolation
from ple.models.attractor import Attractor, AttractorState
from ple.models.finding import Finding

MIN_STABILITY = 0.5

_INSIGHT_TEMPLATES = {
    "coexistence": (
        "The frames {frames} are not mutually exclusive: each holds within "
        "its own domain of '{claim}'. The contradiction marks a domain "
        "boundary, not an error."
    ),
    "hybrid": (
        "The tension between {frames} over '{claim}' is generative: a hybrid "
        "frame subsumes both and explains what neither could alone."
    ),
    "reframed": (
        "The contradiction between {frames} over '{claim}' dissolves at a "
        "higher level of description; the paradox was an artifact of the "
        "framing, and the original frames remain intact beneath it."
    ),
    "emergent": (
        "A novel structure emerged from the sustained tension between "
        "{frames} over '{claim}' that was not predictable from either frame."
    ),
}


def extract(attractor: Attractor, source_paradox_ids: list[str], claim: str, frames: list[str]) -> Finding:
    if attractor.state not in (AttractorState.ACTIVE, AttractorState.STABILIZING):
        raise ContractViolation(
            "findings may only be generated from active/stabilizing attractors"
        )
    if attractor.stability_score < MIN_STABILITY:
        raise ContractViolation(
            f"attractor stability {attractor.stability_score} below the "
            f"finding threshold {MIN_STABILITY} — unstable attractors may "
            "not produce findings"
        )
    if not attractor.basin_nodes:
        raise ContractViolation("attractor basin has not converged")
    if not attractor.lineage:
        raise ContractViolation("attractor lineage is incomplete")

    insight = _INSIGHT_TEMPLATES[attractor.type].format(
        frames=" / ".join(sorted(frames)), claim=claim
    )
    return Finding(
        attractor_id=attractor.attractor_id,
        source_syntheses=attractor.core_syntheses,
        source_paradoxes=tuple(source_paradox_ids),
        insight=insight,
        confidence=attractor.stability_score,
        tension_profile=dict(attractor.tension_profile),
        lineage=attractor.lineage + (attractor.attractor_id,),
    )
