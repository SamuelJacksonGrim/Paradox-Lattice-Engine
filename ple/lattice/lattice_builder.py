"""Stage 3 — lattice construction and update.

Maintains the ParadoxLattice: paradox nodes map 1:1 to ParadoxNodes, frame
nodes represent the frames in tension, contradiction edges connect each
paradox to its frames, and overlap edges connect paradoxes that share a frame.
"""

from __future__ import annotations

from ple.models.lattice import LatticeEdge, LatticeNode, LatticeState, ParadoxLattice
from ple.models.paradox import ParadoxNode
from ple.models.tension_field import TensionField

ACTOR = "lattice_builder"


def initialize() -> ParadoxLattice:
    return ParadoxLattice()


def update_with_paradox(
    lattice: ParadoxLattice,
    paradox: ParadoxNode,
    field: TensionField | None = None,
) -> ParadoxLattice:
    if lattice.state == LatticeState.INITIALIZED:
        lattice.transition(LatticeState.ACTIVE, actor=ACTOR)

    if lattice.find_paradox_node(paradox.paradox_id) is not None:
        _refresh_load(lattice, paradox)
        return lattice

    p_node = lattice.add_node(
        LatticeNode(
            node_type="paradox",
            payload={
                "paradox_id": paradox.paradox_id,
                "contradiction_type": paradox.contradiction_type,
                "frames": sorted(paradox.frames),
                "nested_paradox_ids": list(paradox.nested_paradox_ids),
            },
            tension_load=paradox.intensity,
        ),
        actor=ACTOR,
    )

    for frame in sorted(paradox.frames):
        f_node = lattice.find_frame_node(frame)
        if f_node is None:
            f_node = lattice.add_node(
                LatticeNode(node_type="frame", payload={"frame": frame}),
                actor=ACTOR,
            )
        lattice.add_edge(
            LatticeEdge(
                source=p_node.node_id,
                target=f_node.node_id,
                relation_type="contradiction",
                weight=paradox.intensity,
                tension_transfer=paradox.intensity,
            ),
            actor=ACTOR,
        )

    # Overlap edges: paradoxes sharing a frame influence each other.
    for other in lattice.nodes_of_type("paradox"):
        if other.node_id == p_node.node_id:
            continue
        if set(other.payload["frames"]) & paradox.frames:
            lattice.add_edge(
                LatticeEdge(
                    source=p_node.node_id,
                    target=other.node_id,
                    relation_type="overlap",
                    weight=1.0,
                ),
                actor=ACTOR,
            )

    update_edges(lattice, field)
    return lattice


def update_edges(lattice: ParadoxLattice, field: TensionField | None) -> None:
    """Weight the lattice from field geometry (the lattice layer may read
    field topology and use gradients to weight edges)."""
    if field is None:
        return
    lattice.set_global_tension(field.global_intensity, actor=ACTOR)
    for region in field.regions:
        for pid in region.paradox_ids:
            node = lattice.find_paradox_node(pid)
            if node is not None:
                lattice.update_load(
                    node.node_id, region.tension_density, actor=ACTOR
                )


def _refresh_load(lattice: ParadoxLattice, paradox: ParadoxNode) -> None:
    node = lattice.find_paradox_node(paradox.paradox_id)
    if node is not None:
        lattice.update_load(node.node_id, paradox.intensity, actor=ACTOR)
