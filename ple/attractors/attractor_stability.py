"""Attractor stability — the sole authorized stability_score mutator
(attractor_contract.md §5).

Stability increases with repeated syntheses and decreases when new paradoxes
destabilize the structure. Destabilized attractors attenuate; they are never
deleted.
"""

from __future__ import annotations

from ple.models._mutation import authorized_set
from ple.models.attractor import Attractor, AttractorState

ACTOR = "attractor_stability"

STABILIZING_THRESHOLD = 0.6
ATTENUATION_FLOOR = 0.15


def reinforce(attractor: Attractor, recurrence_count: int) -> float:
    """Stability grows asymptotically toward 1.0 with recurrence."""
    new_score = round(1.0 - 1.0 / (1.0 + 0.75 * recurrence_count), 6)
    authorized_set(attractor, "stability_score", new_score, actor=ACTOR)
    if (
        attractor.state == AttractorState.ACTIVE
        and new_score >= STABILIZING_THRESHOLD
    ):
        attractor.transition(AttractorState.STABILIZING, actor=ACTOR)
    return new_score


def destabilize(attractor: Attractor, shock: float) -> float:
    """New conflicting paradoxes reduce stability; below the floor the
    attractor attenuates (never deletes)."""
    new_score = max(0.0, attractor.stability_score - abs(shock))
    authorized_set(attractor, "stability_score", new_score, actor=ACTOR)
    if new_score < ATTENUATION_FLOOR and attractor.state in (
        AttractorState.ACTIVE,
        AttractorState.STABILIZING,
    ):
        attractor.transition(AttractorState.ATTENUATED, actor=ACTOR)
    return new_score
