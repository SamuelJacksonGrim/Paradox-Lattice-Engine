"""Cross-cutting contract enforcement: the rules every layer must obey."""

import pytest

from ple.errors import ContractViolation, InvalidEvent
from ple import events
from ple.models.attractor import Attractor
from ple.models.finding import Finding
from ple.models.lattice import LatticeEdge, LatticeNode, ParadoxLattice
from ple.models.synthesis import SynthesisRecord
from ple.models.tension_field import TensionField, TensionRegion


class TestForbiddenEvents:
    def test_paradox_cannot_emit_resolved(self):
        with pytest.raises(InvalidEvent):
            events.ParadoxEvent(event_type="resolved", paradox_id="px-1")

    def test_paradox_cannot_emit_deleted(self):
        with pytest.raises(InvalidEvent):
            events.ParadoxEvent(event_type="deleted", paradox_id="px-1")

    def test_finding_cannot_emit_overwritten(self):
        with pytest.raises(InvalidEvent):
            events.FindingEvent(event_type="overwritten", finding_id="fd-1")

    def test_synthesis_cannot_emit_resolved_paradox(self):
        with pytest.raises(InvalidEvent):
            events.SynthesisEvent(event_type="resolved_paradox", synthesis_id="sy-1")


class TestSynthesisContract:
    def test_methods_are_closed_set(self):
        with pytest.raises(ContractViolation):
            SynthesisRecord(
                paradox_ids=("px-1",), method="annihilation",
                resulting_frame="f", quality_score=0.5, tension_reduction=0.5,
            )

    def test_paradox_ids_must_be_non_empty(self):
        with pytest.raises(ContractViolation):
            SynthesisRecord(
                paradox_ids=(), method="coexistence",
                resulting_frame="f", quality_score=0.5, tension_reduction=0.5,
            )

    def test_records_are_immutable(self):
        rec = SynthesisRecord(
            paradox_ids=("px-1",), method="coexistence",
            resulting_frame="f", quality_score=0.5, tension_reduction=0.3,
        )
        with pytest.raises(Exception):
            rec.method = "reframing"


class TestAttractorContract:
    def make(self):
        return Attractor(
            type="coexistence", core_syntheses=("sy-1",), stability_score=0.5,
        )

    def test_types_are_closed_set(self):
        with pytest.raises(ContractViolation):
            Attractor(type="dogma", core_syntheses=("sy-1",), stability_score=0.5)

    def test_core_syntheses_must_be_non_empty(self):
        with pytest.raises(ContractViolation):
            Attractor(type="hybrid", core_syntheses=(), stability_score=0.5)

    def test_only_stability_module_may_update_stability(self):
        from ple.models._mutation import authorized_set
        from ple.errors import UnauthorizedMutation

        attractor = self.make()
        with pytest.raises(UnauthorizedMutation):
            authorized_set(attractor, "stability_score", 0.9, actor="synthesis_engine")

    def test_registry_never_overwrites(self):
        from ple.attractors.attractor_registry import AttractorRegistry

        reg = AttractorRegistry()
        sig = (("a", "b"), "claim", "semantic")
        reg.register(sig, self.make())
        with pytest.raises(ContractViolation):
            reg.register(sig, self.make())


class TestLatticeContract:
    def build(self):
        lattice = ParadoxLattice()
        p = lattice.add_node(
            LatticeNode(node_type="paradox", payload={"paradox_id": "px-1"}),
            actor="lattice_builder",
        )
        f = lattice.add_node(
            LatticeNode(node_type="frame", payload={"frame": "a"}),
            actor="lattice_builder",
        )
        lattice.add_edge(
            LatticeEdge(source=p.node_id, target=f.node_id, relation_type="contradiction"),
            actor="lattice_builder",
        )
        return lattice, p, f

    def test_unauthorized_actor_cannot_mutate(self):
        lattice, _, _ = self.build()
        with pytest.raises(ContractViolation):
            lattice.add_node(
                LatticeNode(node_type="frame", payload={}), actor="rogue_module"
            )

    def test_paradox_nodes_can_never_be_deleted(self):
        lattice, p, _ = self.build()
        with pytest.raises(ContractViolation):
            lattice.remove_node(p.node_id, actor="lattice_simplifier")

    def test_synthesis_layer_may_only_add_synthesis_nodes(self):
        lattice, _, _ = self.build()
        with pytest.raises(ContractViolation):
            lattice.add_node(
                LatticeNode(node_type="paradox", payload={}),
                actor="synthesis_engine",
            )

    def test_self_edges_forbidden(self):
        lattice, p, _ = self.build()
        with pytest.raises(ContractViolation):
            LatticeEdge(source=p.node_id, target=p.node_id, relation_type="overlap")

    def test_invalid_node_type_rejected(self):
        with pytest.raises(ContractViolation):
            LatticeNode(node_type="opinion", payload={})


class TestFieldContract:
    def test_regions_require_paradoxes(self):
        with pytest.raises(ContractViolation):
            TensionRegion(paradox_ids=(), tension_density=0.5, coherence_score=0.5)

    def test_regions_require_nonzero_density(self):
        with pytest.raises(ContractViolation):
            TensionRegion(paradox_ids=("px-1",), tension_density=0.0, coherence_score=0.5)

    def test_field_requires_regions(self):
        with pytest.raises(ContractViolation):
            TensionField(regions=(), global_intensity=0.5)

    def test_no_self_neighbors(self):
        with pytest.raises(ContractViolation):
            TensionRegion(
                region_id="rg-x", paradox_ids=("px-1",),
                tension_density=0.5, coherence_score=0.5, neighbors=("rg-x",),
            )


class TestFindingContract:
    def make(self):
        return Finding(
            attractor_id="at-1", source_syntheses=("sy-1",),
            source_paradoxes=("px-1",), insight="a real insight", confidence=0.7,
        )

    def test_requires_sources(self):
        with pytest.raises(ContractViolation):
            Finding(
                attractor_id="at-1", source_syntheses=(),
                source_paradoxes=("px-1",), insight="x", confidence=0.5,
            )

    def test_insight_is_immutable(self):
        finding = self.make()
        with pytest.raises(Exception):
            finding.insight = "rewritten"

    def test_only_validator_may_set_status(self):
        from ple.models._mutation import authorized_set
        from ple.errors import UnauthorizedMutation

        finding = self.make()
        with pytest.raises(UnauthorizedMutation):
            authorized_set(finding, "validation_status", "validated", actor="memory")


class TestMemoryContract:
    def test_findings_never_overwritten(self):
        from ple.memory.paradox_memory_buffer import ParadoxMemoryBuffer

        buf = ParadoxMemoryBuffer()
        finding = Finding(
            attractor_id="at-1", source_syntheses=("sy-1",),
            source_paradoxes=("px-1",), insight="insight", confidence=0.5,
        )
        buf.store_finding(finding)
        with pytest.raises(ContractViolation):
            buf.store_finding(finding)
