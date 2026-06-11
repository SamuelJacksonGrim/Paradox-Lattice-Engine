"""ParadoxLattice, LatticeNode, LatticeEdge models — see lattice_contract.md."""

from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass, field

from ple.errors import ContractViolation, InvalidLifecycleTransition
from ple.models._mutation import authorized_set

NODE_TYPES = frozenset({"paradox", "frame", "synthesis", "attractor"})
EDGE_TYPES = frozenset(
    {"contradiction", "overlap", "synthesis", "dependency", "attractor_link"}
)


class LatticeState(str, enum.Enum):
    INITIALIZED = "initialized"
    ACTIVE = "active"
    EXPANDED = "expanded"
    SIMPLIFIED = "simplified"
    STABILIZED = "stabilized"
    ARCHIVED = "archived"


_TRANSITIONS: dict[tuple[LatticeState, LatticeState], frozenset[str]] = {
    (LatticeState.INITIALIZED, LatticeState.ACTIVE): frozenset({"lattice_builder"}),
    (LatticeState.ACTIVE, LatticeState.EXPANDED): frozenset({"lattice_builder"}),
    (LatticeState.EXPANDED, LatticeState.ACTIVE): frozenset({"lattice_builder"}),
    (LatticeState.ACTIVE, LatticeState.SIMPLIFIED): frozenset(
        {"lattice_simplifier"}
    ),
    (LatticeState.EXPANDED, LatticeState.SIMPLIFIED): frozenset(
        {"lattice_simplifier"}
    ),
    (LatticeState.SIMPLIFIED, LatticeState.ACTIVE): frozenset({"lattice_builder"}),
    (LatticeState.SIMPLIFIED, LatticeState.STABILIZED): frozenset(
        {"attractor_evolution"}
    ),
    (LatticeState.ACTIVE, LatticeState.STABILIZED): frozenset(
        {"attractor_evolution"}
    ),
    (LatticeState.STABILIZED, LatticeState.ARCHIVED): frozenset({"memory"}),
    (LatticeState.ACTIVE, LatticeState.ARCHIVED): frozenset({"memory"}),
    (LatticeState.SIMPLIFIED, LatticeState.ARCHIVED): frozenset({"memory"}),
}


@dataclass(frozen=True)
class LatticeNode:
    """Immutable except for tension_load and stability_score (lattice_contract.md §2)."""

    node_type: str
    payload: dict = field(default_factory=dict)
    tension_load: float = 0.0
    stability_score: float = 0.0
    node_id: str = field(default_factory=lambda: f"ln-{uuid.uuid4().hex[:12]}")

    def __post_init__(self) -> None:
        if self.node_type not in NODE_TYPES:
            raise ContractViolation(
                f"invalid lattice node type {self.node_type!r}; "
                f"must be one of {sorted(NODE_TYPES)}"
            )


@dataclass(frozen=True)
class LatticeEdge:
    source: str
    target: str
    relation_type: str
    weight: float = 1.0
    tension_transfer: float = 0.0
    edge_id: str = field(default_factory=lambda: f"le-{uuid.uuid4().hex[:12]}")

    def __post_init__(self) -> None:
        if self.relation_type not in EDGE_TYPES:
            raise ContractViolation(
                f"invalid edge relation type {self.relation_type!r}"
            )
        if self.source == self.target:
            raise ContractViolation("edges must not be self-referential")
        if self.weight < 0.0 or self.tension_transfer < 0.0:
            raise ContractViolation("edge weight and tension_transfer must be >= 0")


class ParadoxLattice:
    """The structural paradox graph.

    Mutable only through lattice_builder, lattice_simplifier, multi_frame_index,
    and attractor_evolution (lattice_contract.md §5). Those processors call the
    _add/_update methods below, declaring themselves as actors; everything else
    gets a read-only view.
    """

    _MUTATORS = frozenset(
        {
            "lattice_builder",
            "lattice_simplifier",
            "multi_frame_index",
            "attractor_evolution",
            "synthesis_engine",  # may add synthesis nodes/edges only
        }
    )

    def __init__(self) -> None:
        self.lattice_id = f"lt-{uuid.uuid4().hex[:12]}"
        self._nodes: dict[str, LatticeNode] = {}
        self._edges: dict[str, LatticeEdge] = {}
        self.global_tension: float = 0.0
        self.resolution_horizons: list[str] = []
        self.state = LatticeState.INITIALIZED

    # -- read-only access -------------------------------------------------
    @property
    def nodes(self) -> tuple[LatticeNode, ...]:
        return tuple(self._nodes.values())

    @property
    def edges(self) -> tuple[LatticeEdge, ...]:
        return tuple(self._edges.values())

    def get_node(self, node_id: str) -> LatticeNode | None:
        return self._nodes.get(node_id)

    def nodes_of_type(self, node_type: str) -> tuple[LatticeNode, ...]:
        return tuple(n for n in self._nodes.values() if n.node_type == node_type)

    def edges_for(self, node_id: str) -> tuple[LatticeEdge, ...]:
        return tuple(
            e
            for e in self._edges.values()
            if e.source == node_id or e.target == node_id
        )

    def find_paradox_node(self, paradox_id: str) -> LatticeNode | None:
        for n in self.nodes_of_type("paradox"):
            if n.payload.get("paradox_id") == paradox_id:
                return n
        return None

    def find_frame_node(self, frame: str) -> LatticeNode | None:
        for n in self.nodes_of_type("frame"):
            if n.payload.get("frame") == frame:
                return n
        return None

    # -- guarded mutation -------------------------------------------------
    def _check_actor(self, actor: str) -> None:
        if actor not in self._MUTATORS:
            raise ContractViolation(
                f"actor '{actor}' may not mutate the lattice; "
                "only lattice processors may (lattice_contract.md §5)"
            )

    def add_node(self, node: LatticeNode, *, actor: str) -> LatticeNode:
        self._check_actor(actor)
        if actor == "synthesis_engine" and node.node_type not in (
            "synthesis",
            "attractor",
        ):
            raise ContractViolation(
                "synthesis layer may add only synthesis nodes / attractor "
                "candidates to the lattice"
            )
        self._nodes[node.node_id] = node
        return node

    def add_edge(self, edge: LatticeEdge, *, actor: str) -> LatticeEdge:
        self._check_actor(actor)
        if edge.source not in self._nodes or edge.target not in self._nodes:
            raise ContractViolation("edges must connect existing nodes")
        self._edges[edge.edge_id] = edge
        return edge

    def remove_node(self, node_id: str, *, actor: str) -> None:
        """Only non-paradox, non-attractor nodes may ever be removed, and only
        by the simplifier when merging duplicates (lattice_contract.md §5)."""
        self._check_actor(actor)
        if actor != "lattice_simplifier":
            raise ContractViolation("only lattice_simplifier may remove nodes")
        node = self._nodes.get(node_id)
        if node is None:
            return
        if node.node_type == "paradox":
            raise ContractViolation("paradox nodes must never be deleted")
        if node.node_type == "attractor":
            raise ContractViolation("attractor nodes must never be deleted")
        del self._nodes[node_id]
        self._edges = {
            eid: e
            for eid, e in self._edges.items()
            if e.source != node_id and e.target != node_id
        }

    def update_load(
        self, node_id: str, tension_load: float, *, actor: str
    ) -> None:
        self._check_actor(actor)
        node = self._nodes[node_id]
        authorized_set(node, "tension_load", max(0.0, tension_load), actor=actor)

    def update_stability(
        self, node_id: str, stability_score: float, *, actor: str
    ) -> None:
        self._check_actor(actor)
        node = self._nodes[node_id]
        authorized_set(
            node,
            "stability_score",
            min(1.0, max(0.0, stability_score)),
            actor=actor,
        )

    def set_global_tension(self, value: float, *, actor: str) -> None:
        self._check_actor(actor)
        self.global_tension = max(0.0, value)

    def transition(self, new_state: LatticeState, *, actor: str) -> None:
        key = (self.state, new_state)
        allowed = _TRANSITIONS.get(key)
        if allowed is None:
            raise InvalidLifecycleTransition(
                f"lattice transition {self.state.value} -> {new_state.value} "
                "is not permitted"
            )
        if actor not in allowed:
            raise InvalidLifecycleTransition(
                f"actor '{actor}' may not perform lattice transition "
                f"{self.state.value} -> {new_state.value}"
            )
        self.state = new_state

    def snapshot(self) -> dict:
        """Frozen copy for memory (memory_contract.md §5)."""
        return {
            "snapshot_id": f"ls-{uuid.uuid4().hex[:12]}",
            "lattice_id": self.lattice_id,
            "state": self.state.value,
            "global_tension": self.global_tension,
            "nodes": tuple(
                {
                    "node_id": n.node_id,
                    "node_type": n.node_type,
                    "payload": dict(n.payload),
                    "tension_load": n.tension_load,
                    "stability_score": n.stability_score,
                }
                for n in self._nodes.values()
            ),
            "edges": tuple(
                {
                    "edge_id": e.edge_id,
                    "source": e.source,
                    "target": e.target,
                    "relation_type": e.relation_type,
                    "weight": e.weight,
                    "tension_transfer": e.tension_transfer,
                }
                for e in self._edges.values()
            ),
        }
