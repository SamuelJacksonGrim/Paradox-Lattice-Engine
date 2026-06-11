"""Resolution horizon modeling — predicting collapse vs persistence."""

from __future__ import annotations

from ple.models.horizon import ResolutionHorizon
from ple.models.paradox import ParadoxNode
from ple.models.tension_field import TensionField


def update_from_field(
    field: TensionField, paradoxes: list[ParadoxNode]
) -> list[ResolutionHorizon]:
    """Build horizons for regions whose tension is low enough that collapse
    is plausible but has not occurred. Low intensity -> higher collapse
    probability; hot paradoxes persist."""
    by_id = {p.paradox_id: p for p in paradoxes}
    horizons: list[ResolutionHorizon] = []
    for region in field.regions:
        nodes = [by_id[pid] for pid in region.paradox_ids if pid in by_id]
        if not nodes:
            continue
        mean_intensity = sum(n.intensity for n in nodes) / len(nodes)
        horizons.append(
            ResolutionHorizon(
                paradox_ids=tuple(n.paradox_id for n in nodes),
                collapse_probability=round(max(0.0, 1.0 - mean_intensity), 6),
                stability_window={"start": 0.0, "end": mean_intensity},
                triggers=("tension_reduction", "synthesis_recurrence"),
            )
        )
    return horizons
