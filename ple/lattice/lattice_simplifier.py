"""Lattice simplification — merge duplicate non-paradox nodes while
preserving paradox topology (lattice_contract.md: forbidden to delete or
merge paradox nodes, or collapse nested paradoxes).
"""

from __future__ import annotations

from ple.models.lattice import LatticeEdge, LatticeState, ParadoxLattice

ACTOR = "lattice_simplifier"


def simplify(lattice: ParadoxLattice) -> ParadoxLattice:
    """Merge frame nodes that represent the same frame (duplicates can arise
    from multi-frame indexing); paradox/synthesis/attractor structure is
    untouched."""
    seen: dict[str, str] = {}
    duplicates: list[tuple[str, str]] = []
    for node in lattice.nodes_of_type("frame"):
        frame = node.payload.get("frame")
        if frame in seen:
            duplicates.append((node.node_id, seen[frame]))
        else:
            seen[frame] = node.node_id

    for dup_id, keep_id in duplicates:
        for edge in lattice.edges_for(dup_id):
            source = keep_id if edge.source == dup_id else edge.source
            target = keep_id if edge.target == dup_id else edge.target
            if source != target:
                lattice.add_edge(
                    LatticeEdge(
                        source=source,
                        target=target,
                        relation_type=edge.relation_type,
                        weight=edge.weight,
                        tension_transfer=edge.tension_transfer,
                    ),
                    actor=ACTOR,
                )
        lattice.remove_node(dup_id, actor=ACTOR)

    if duplicates and lattice.state in (LatticeState.ACTIVE, LatticeState.EXPANDED):
        lattice.transition(LatticeState.SIMPLIFIED, actor=ACTOR)
    return lattice
