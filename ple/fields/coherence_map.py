"""Coherence map processor — the only module that may update coherence
(field_contract.md §4). Coherence increases when synthesis reduces tension.
"""

from __future__ import annotations

from ple.models.paradox import ParadoxNode
from ple.models.tension_field import TensionField
from ple.fields.tension_field_generator import compute_coherence


def update(field: TensionField, paradoxes: list[ParadoxNode]) -> None:
    """Recompute coherence in place from the current paradox distribution.

    The coherence_map dict is mutated (fields are mutable through approved
    processors); the recomputation is always derived from paradox intensity,
    never manually edited.
    """
    fresh = compute_coherence(
        [p for p in paradoxes if p.paradox_id in field.paradox_ids]
    )
    field.coherence_map.clear()
    field.coherence_map.update(fresh)
