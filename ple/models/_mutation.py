"""Authorized mutation gateway for frozen PLE models.

The contracts make most objects immutable except for narrowly-scoped fields
that may only be touched by specific processors (e.g. ParadoxNode.intensity
by the paradox intensity model, Attractor.stability_score by the attractor
stability module). Frozen dataclasses enforce immutability for everyone;
authorized processors route their permitted writes through `authorized_set`,
declaring who they are. The actor registry below is the single source of
truth for which actor may write which field on which type.
"""

from __future__ import annotations

from typing import Any

from ple.errors import UnauthorizedMutation

# (type name, field name) -> set of actor names permitted to write it.
_AUTHORIZED: dict[tuple[str, str], frozenset[str]] = {
    ("ParadoxNode", "intensity"): frozenset({"paradox_intensity_model"}),
    ("ParadoxNode", "lineage"): frozenset(
        {"paradox_normalizer", "synthesis_engine", "attractor_evolution"}
    ),
    ("ParadoxNode", "nested_paradox_ids"): frozenset({"paradox_normalizer"}),
    ("ParadoxNode", "state"): frozenset(
        {"paradox_layer", "synthesis_engine", "attractor_evolution", "memory"}
    ),
    ("LatticeNode", "tension_load"): frozenset(
        {"lattice_builder", "synthesis_engine"}
    ),
    ("LatticeNode", "stability_score"): frozenset(
        {"lattice_builder", "synthesis_engine", "attractor_evolution"}
    ),
    ("Attractor", "stability_score"): frozenset({"attractor_stability"}),
    ("Attractor", "basin_nodes"): frozenset({"attractor_evolution"}),
    ("Attractor", "lineage"): frozenset({"attractor_evolution"}),
    ("Attractor", "state"): frozenset(
        {
            "synthesis_engine",
            "attractor_detector",
            "attractor_evolution",
            "attractor_stability",
            "memory",
        }
    ),
    ("Finding", "validation_status"): frozenset({"finding_validator"}),
    ("Finding", "confidence"): frozenset({"finding_validator"}),
    ("Finding", "export_metadata"): frozenset({"finding_export"}),
    ("SynthesisRecord", "state"): frozenset(
        {"synthesis_engine", "attractor_detector"}
    ),
    ("TensionField", "state"): frozenset(
        {"tension_field_generator", "synthesis_engine", "attractor_evolution", "memory"}
    ),
    ("ParadoxLattice", "state"): frozenset(
        {"lattice_builder", "lattice_simplifier", "attractor_evolution", "memory"}
    ),
}


def authorized_set(obj: Any, field: str, value: Any, *, actor: str) -> None:
    """Write `field` on a frozen model instance on behalf of `actor`.

    Raises UnauthorizedMutation if the (type, field) pair is not registered
    or the actor is not on its allowlist.
    """
    key = (type(obj).__name__, field)
    allowed = _AUTHORIZED.get(key)
    if allowed is None:
        raise UnauthorizedMutation(
            f"{key[0]}.{field} is immutable under the PLE contracts"
        )
    if actor not in allowed:
        raise UnauthorizedMutation(
            f"actor '{actor}' may not mutate {key[0]}.{field}; "
            f"authorized: {sorted(allowed)}"
        )
    object.__setattr__(obj, field, value)


def extend_lineage(obj: Any, entries: list[str], *, actor: str) -> None:
    """Append-only lineage extension (monotonic lineage rule)."""
    current = list(getattr(obj, "lineage"))
    authorized_set(obj, "lineage", tuple(current + list(entries)), actor=actor)
