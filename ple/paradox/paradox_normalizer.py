"""Stage 1d — normalization of raw contradictions into canonical ParadoxNodes."""

from __future__ import annotations

from ple.models.paradox import ParadoxNode, ParadoxState
from ple.paradox.paradox_detector import RawContradiction

ACTOR = "paradox_normalizer"
LAYER = "paradox_layer"


def to_paradox_node(
    contradiction: RawContradiction,
    contradiction_type: str,
    intensity: float,
    context: dict | None = None,
) -> ParadoxNode:
    """Build a canonical ParadoxNode and walk it detected -> normalized -> active."""
    context = dict(context or contradiction.context)
    context.setdefault("claim_key", contradiction.claim_key)

    node = ParadoxNode(
        frame_a=contradiction.frame_a,
        frame_b=contradiction.frame_b,
        contradiction_type=contradiction_type,
        intensity=intensity,
        context_window=context,
        supporting_evidence=tuple(context.get("supporting_evidence", ())),
        opposing_evidence=tuple(context.get("opposing_evidence", ())),
        lineage=(
            f"detected:{contradiction.frame_a}~{contradiction.frame_b}"
            f":{contradiction.claim_key}",
        ),
    )
    node.transition(ParadoxState.NORMALIZED, actor=LAYER)
    node.transition(ParadoxState.ACTIVE, actor=LAYER)
    return node


def nest(parent: ParadoxNode, child: ParadoxNode) -> None:
    """Cross-frame paradox merging: when the same claim conflicts across
    three or more frames, the hottest pairwise paradox becomes the parent
    and the others nest beneath it (paradox_contract.md §3). The parent
    stays valid, the children are never flattened, and lineage records the
    nesting.
    """
    from ple.errors import ContractViolation
    from ple.models._mutation import authorized_set, extend_lineage

    if child.paradox_id == parent.paradox_id:
        raise ContractViolation("a paradox cannot nest inside itself")
    if child.paradox_id in parent.nested_paradox_ids:
        return
    authorized_set(
        parent,
        "nested_paradox_ids",
        parent.nested_paradox_ids + (child.paradox_id,),
        actor=ACTOR,
    )
    extend_lineage(parent, [f"nested:{child.paradox_id}"], actor=ACTOR)


def signature(node: ParadoxNode) -> tuple:
    """Stable identity for recurrence detection: same frames + claim + type."""
    return (
        frozenset({node.frame_a, node.frame_b}),
        node.context_window.get("claim_key"),
        node.contradiction_type,
    )
