"""Tension collapse prediction — which paradoxes are heading toward
collapse, and which will persist (Phase 3: collapse prediction).

A paradox "collapses" when synthesis has drained its tension to the point
where it no longer exerts bidirectional pressure. Collapse is predicted,
never forced: resolution is optional, and premature collapse is a named
failure mode. The predictor only classifies trajectories and emits
ResolutionHorizons; the actual attenuation transition is performed by the
synthesis layer (an authorized actor) when a collapse is confirmed.
"""

from __future__ import annotations

from collections import defaultdict

from ple.models.horizon import ResolutionHorizon
from ple.models.paradox import ParadoxNode, ParadoxState

ACTOR = "tension_collapse_predictor"

COLLAPSE_INTENSITY = 0.05  # below this, tension no longer sustains the paradox
TREND_WINDOW = 3


class TensionCollapsePredictor:
    """Tracks per-paradox intensity trajectories across pipeline runs."""

    def __init__(self) -> None:
        self._trajectories: dict[str, list[float]] = defaultdict(list)

    def observe(self, paradox: ParadoxNode) -> None:
        self._trajectories[paradox.paradox_id].append(paradox.intensity)

    def trajectory(self, paradox_id: str) -> tuple[float, ...]:
        return tuple(self._trajectories[paradox_id])

    def collapse_probability(self, paradox: ParadoxNode) -> float:
        """Probability the paradox collapses rather than persists, from its
        current intensity and recent trend."""
        history = self._trajectories[paradox.paradox_id]
        if not history:
            return 0.0
        recent = history[-TREND_WINDOW:]
        trend = recent[-1] - recent[0]  # negative = draining
        base = 1.0 - paradox.intensity
        trend_term = max(0.0, -trend)  # only decline raises collapse odds
        return round(min(1.0, max(0.0, 0.7 * base + 0.3 * trend_term)), 6)

    def classify(self, paradox: ParadoxNode) -> str:
        """One of: collapsed | stabilized | deferred (the valid
        ResolutionEvent types)."""
        if paradox.intensity < COLLAPSE_INTENSITY:
            return "collapsed"
        history = self._trajectories[paradox.paradox_id]
        if len(history) >= 2 and history[-1] > history[-2]:
            return "deferred"  # re-intensifying; resolution pushed out
        return "stabilized"  # persistent tension at a steady level

    def predict(self, paradoxes: list[ParadoxNode]) -> list[ResolutionHorizon]:
        return [
            ResolutionHorizon(
                paradox_ids=(p.paradox_id,),
                collapse_probability=self.collapse_probability(p),
                stability_window={"start": 0.0, "end": p.intensity},
                triggers=("tension_reduction", "synthesis_recurrence"),
            )
            for p in paradoxes
        ]


def confirm_collapse(paradox: ParadoxNode) -> bool:
    """Attenuate a paradox whose tension has fully drained. Performed on
    behalf of the synthesis layer — the contract's authorized attenuator.
    The paradox remains structurally intact and queryable; it is never
    resolved or deleted, and re-encountering its contradiction reactivates it.
    """
    if (
        paradox.state == ParadoxState.ACTIVE
        and paradox.intensity < COLLAPSE_INTENSITY
    ):
        paradox.transition(ParadoxState.ATTENUATED, actor="synthesis_engine")
        return True
    return False
