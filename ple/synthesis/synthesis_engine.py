"""Stage 4 — synthesis pass.

Transforms structured tension into SynthesisRecords without erasing the
contradictions that generated them (the synthesis prime directive). Method
selection follows the contradiction's character:

- contextual  -> coexistence   (partition domains; both frames stay valid)
- logical     -> coexistence   (opposed booleans hold in partitioned scopes)
- semantic    -> hybridization (a new frame blends the inputs)
- self_referential -> reframing (dissolves at a higher-order level, marked
                                 as reframed, never silently discarded)
"""

from __future__ import annotations

from ple.fields import coherence_map
from ple.models.lattice import LatticeEdge, LatticeNode, ParadoxLattice
from ple.models.paradox import ParadoxNode
from ple.models.synthesis import SynthesisRecord, SynthesisState
from ple.models.tension_field import TensionField
from ple.paradox import paradox_intensity_model

ACTOR = "synthesis_engine"

_METHOD_FOR_TYPE = {
    "contextual": "coexistence",
    "logical": "coexistence",
    "semantic": "hybridization",
    "self_referential": "reframing",
}

# How much tension each method drains from its paradoxes.
_REDUCTION = {"coexistence": 0.30, "hybridization": 0.45, "reframing": 0.55}


def find_candidates(
    lattice: ParadoxLattice,
    field: TensionField,
    paradoxes: list[ParadoxNode],
) -> list[ParadoxNode]:
    """Synthesis candidates: active, valid paradoxes present in both the
    lattice and the field (locality rule: operate on a well-defined subset)."""
    in_field = field.paradox_ids
    return [
        p
        for p in paradoxes
        if p.is_valid
        and p.paradox_id in in_field
        and lattice.find_paradox_node(p.paradox_id) is not None
    ]


def synthesize(
    paradox: ParadoxNode,
    lattice: ParadoxLattice,
    field: TensionField,
) -> SynthesisRecord:
    method = _METHOD_FOR_TYPE[paradox.contradiction_type]
    reduction = _REDUCTION[method]
    resulting_frame = _resulting_frame(paradox, method)

    record = SynthesisRecord(
        paradox_ids=(paradox.paradox_id,),
        method=method,
        resulting_frame=resulting_frame,
        quality_score=round(min(1.0, 0.4 + paradox.intensity * 0.5), 6),
        tension_reduction=reduction,
        # Traceability rule: inputs traceable from the record.
        lineage=(paradox.paradox_id,) + paradox.lineage,
    )

    _write_to_lattice(record, paradox, lattice)
    _attenuate_tension(record, paradox, field)
    record.transition(SynthesisState.EVALUATED, actor=ACTOR)
    return record


def _resulting_frame(paradox: ParadoxNode, method: str) -> str:
    a, b = sorted(paradox.frames)
    claim = paradox.context_window.get("claim_key", "claim")
    if method == "coexistence":
        return f"{a} and {b} hold in partitioned domains of '{claim}'"
    if method == "hybridization":
        return f"hybrid({a}+{b}) over '{claim}'"
    return f"reframed: '{claim}' reinterpreted above {a}/{b}"


def _write_to_lattice(
    record: SynthesisRecord, paradox: ParadoxNode, lattice: ParadoxLattice
) -> None:
    """Create the synthesis node and its edges (synthesis_contract.md §6).

    Synthesis nodes are content-addressed: a re-encountered contradiction
    reuses the existing node for its synthesis shape rather than adding an
    identical one each cycle. This keeps the live lattice bounded under
    recurrence (the synthesis *history* in memory still records every
    encounter, so attractor recurrence detection is unaffected) and avoids
    duplicate edges that would otherwise accumulate without bound.
    """
    s_node = lattice.find_synthesis_node(record.method, record.resulting_frame)
    if s_node is None:
        s_node = lattice.add_node(
            LatticeNode(
                node_type="synthesis",
                payload={
                    "synthesis_id": record.synthesis_id,
                    "method": record.method,
                    "resulting_frame": record.resulting_frame,
                },
                stability_score=record.quality_score,
            ),
            actor=ACTOR,
        )
    p_node = lattice.find_paradox_node(paradox.paradox_id)
    if not lattice.has_edge(p_node.node_id, s_node.node_id, "synthesis"):
        lattice.add_edge(
            LatticeEdge(
                source=p_node.node_id,
                target=s_node.node_id,
                relation_type="synthesis",
                weight=record.quality_score,
                tension_transfer=record.tension_reduction,
            ),
            actor=ACTOR,
        )
    for frame in sorted(paradox.frames):
        f_node = lattice.find_frame_node(frame)
        if f_node is not None and not lattice.has_edge(
            f_node.node_id, s_node.node_id, "dependency"
        ):
            lattice.add_edge(
                LatticeEdge(
                    source=f_node.node_id,
                    target=s_node.node_id,
                    relation_type="dependency",
                    weight=1.0,
                ),
                actor=ACTOR,
            )
    # Reduce tension_load on the connected paradox node.
    lattice.update_load(
        p_node.node_id,
        p_node.tension_load * (1.0 - record.tension_reduction),
        actor=ACTOR,
    )


def _attenuate_tension(
    record: SynthesisRecord, paradox: ParadoxNode, field: TensionField
) -> None:
    """Synthesis reduces tension density and raises coherence — but routes
    intensity changes through the intensity model (the only authorized
    mutator) and coherence changes through the coherence_map processor."""
    paradox_intensity_model.attenuate(paradox, record.tension_reduction)
    coherence_map.update(field, [paradox])
