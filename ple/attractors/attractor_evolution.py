"""Attractor evolution — forming -> active promotion and basin expansion.

Only this module may expand basins or extend attractor lineage
(attractor_contract.md §4, §7).
"""

from __future__ import annotations

from ple.models._mutation import authorized_set, extend_lineage
from ple.models.attractor import Attractor, AttractorState
from ple.models.lattice import LatticeEdge, LatticeNode, ParadoxLattice

ACTOR = "attractor_evolution"


def activate(attractor: Attractor, lattice: ParadoxLattice) -> Attractor:
    """Promote forming -> active, add the attractor node to the lattice, and
    seed its basin with the connected paradox/frame/synthesis nodes."""
    a_node = lattice.add_node(
        LatticeNode(
            node_type="attractor",
            payload={
                "attractor_id": attractor.attractor_id,
                "type": attractor.type,
            },
            stability_score=attractor.stability_score,
        ),
        actor=ACTOR,
    )

    basin: list[str] = [a_node.node_id]
    for synthesis_id in attractor.core_syntheses:
        for node in lattice.nodes_of_type("synthesis"):
            if node.payload.get("synthesis_id") == synthesis_id:
                basin.append(node.node_id)
                lattice.add_edge(
                    LatticeEdge(
                        source=node.node_id,
                        target=a_node.node_id,
                        relation_type="attractor_link",
                        weight=1.0,
                    ),
                    actor=ACTOR,
                )
                # Pull connected paradox/frame nodes into the basin.
                for edge in lattice.edges_for(node.node_id):
                    other = (
                        edge.target if edge.source == node.node_id else edge.source
                    )
                    other_node = lattice.get_node(other)
                    if (
                        other_node is not None
                        and other_node.node_type in ("paradox", "frame")
                        and other not in basin
                    ):
                        basin.append(other)

    authorized_set(attractor, "basin_nodes", tuple(basin), actor=ACTOR)
    attractor.transition(AttractorState.ACTIVE, actor=ACTOR)
    return attractor


def expand_basin(
    attractor: Attractor, node_ids: list[str], lattice: ParadoxLattice
) -> None:
    """Basin expansion — append-only, connected nodes only."""
    current = list(attractor.basin_nodes)
    additions = [n for n in node_ids if n not in current and lattice.get_node(n)]
    if additions:
        authorized_set(
            attractor, "basin_nodes", tuple(current + additions), actor=ACTOR
        )


def record_recurrence(attractor: Attractor, synthesis_id: str) -> None:
    """Extend lineage when the pattern recurs (monotonic lineage rule)."""
    extend_lineage(attractor, [synthesis_id], actor=ACTOR)
