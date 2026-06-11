"""Attractor detection — recurrence is the defining signal.

Repeated similar syntheses (same paradox signature + method) are promoted to
attractor candidates; the detector is the only module that may promote
candidate -> forming (attractor_contract.md §6).
"""

from __future__ import annotations

from collections import defaultdict

from ple.attractors.attractor_registry import AttractorRegistry
from ple.models.attractor import Attractor, AttractorState
from ple.models.synthesis import SynthesisRecord, SynthesisState

ACTOR = "attractor_detector"

# synthesis method -> attractor type
_ATTRACTOR_TYPE = {
    "coexistence": "coexistence",
    "hybridization": "hybrid",
    "reframing": "reframed",
}

RECURRENCE_THRESHOLD = 2


class AttractorDetector:
    def __init__(self, registry: AttractorRegistry) -> None:
        self._registry = registry
        self._recurrence: dict[tuple, list[SynthesisRecord]] = defaultdict(list)

    def observe(
        self, paradox_signature: tuple, record: SynthesisRecord
    ) -> Attractor | None:
        """Track a synthesis; when recurrence crosses threshold, promote the
        records to candidates and create the attractor (candidate -> forming).
        Returns the attractor when one is detected or already exists."""
        key = (paradox_signature, record.method)
        self._recurrence[key].append(record)

        existing = self._registry.get(key)
        if existing is not None:
            return existing

        history = self._recurrence[key]
        if len(history) < RECURRENCE_THRESHOLD:
            return None

        for rec in history:
            if rec.state == SynthesisState.EVALUATED:
                rec.transition(
                    SynthesisState.PROMOTED_TO_CANDIDATE, actor=ACTOR
                )

        attractor = Attractor(
            type=_ATTRACTOR_TYPE[record.method],
            core_syntheses=tuple(r.synthesis_id for r in history),
            stability_score=0.0,
            tension_profile={
                "mean_tension_reduction": sum(r.tension_reduction for r in history)
                / len(history)
            },
            # Lineage continuity: synthesis + paradox ancestry.
            lineage=tuple(
                pid for r in history for pid in r.paradox_ids
            )
            + tuple(r.synthesis_id for r in history),
        )
        self._registry.register(key, attractor)
        attractor.transition(AttractorState.FORMING, actor=ACTOR)
        return attractor

    def recurrence_count(self, paradox_signature: tuple, method: str) -> int:
        return len(self._recurrence[(paradox_signature, method)])
