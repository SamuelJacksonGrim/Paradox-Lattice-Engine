"""End-to-end: contradiction -> paradox -> tension -> lattice -> synthesis
-> attractor -> finding -> memory.
"""

import pytest

from ple import ParadoxLatticeEngine
from ple.models.attractor import AttractorState
from ple.models.paradox import ParadoxState
from ple.models.synthesis import SynthesisState

WAVE = {"name": "wave_theory", "claims": {"light_is": "a wave"}}
PARTICLE = {"name": "particle_theory", "claims": {"light_is": "a particle"}}
AGREE = {"name": "agreeing", "claims": {"light_is": "a wave"}}


@pytest.fixture
def engine():
    return ParadoxLatticeEngine()


class TestDormancy:
    def test_no_contradiction_means_no_activation(self, engine):
        result = engine.process(WAVE, AGREE)
        assert not result.triggered
        assert result.tension_field is None
        assert engine.memory.episodes == ()


class TestSingleEncounter:
    def test_full_first_pass(self, engine):
        result = engine.process(WAVE, PARTICLE)

        assert result.triggered
        node = result.paradox_nodes[0]
        assert node.state == ParadoxState.ACTIVE
        assert node.contradiction_type == "semantic"

        # Tension field grounded in the paradox.
        assert node.paradox_id in result.tension_field.paradox_ids
        assert result.tension_field.global_intensity > 0

        # Lattice has paradox, frames, and synthesis nodes.
        assert result.lattice.find_paradox_node(node.paradox_id) is not None
        assert result.lattice.find_frame_node("wave_theory") is not None
        assert len(result.lattice.nodes_of_type("synthesis")) == 1

        # Synthesis happened but no attractor yet (no recurrence).
        assert len(result.syntheses) == 1
        assert result.syntheses[0].method == "hybridization"
        assert result.attractors == []
        assert result.findings == []

        # Episode stored.
        assert len(engine.memory.episodes) == 1
        assert result.episode.resolution_state == "unresolved"

    def test_synthesis_attenuates_but_never_erases_paradox(self, engine):
        result = engine.process(WAVE, PARTICLE)
        node = result.paradox_nodes[0]
        # Intensity reduced by synthesis, paradox still alive and in lattice.
        assert 0 < node.intensity < 1
        assert node.state == ParadoxState.ACTIVE
        assert result.lattice.find_paradox_node(node.paradox_id) is not None


class TestRecurrenceFormsAttractor:
    def test_second_encounter_creates_attractor(self, engine):
        engine.process(WAVE, PARTICLE)
        result = engine.process(WAVE, PARTICLE)

        assert len(result.attractors) == 1
        attractor = result.attractors[0]
        assert attractor.type == "hybrid"
        assert attractor.state in (AttractorState.ACTIVE, AttractorState.STABILIZING)
        assert attractor.basin_nodes  # basin converged
        # Core syntheses were promoted to candidates.
        promoted = [
            s for s in engine.memory.synthesis_history
            if s.state == SynthesisState.PROMOTED_TO_CANDIDATE
        ]
        assert len(promoted) >= 2

    def test_attractor_node_lands_in_lattice(self, engine):
        engine.process(WAVE, PARTICLE)
        result = engine.process(WAVE, PARTICLE)
        assert len(result.lattice.nodes_of_type("attractor")) == 1


class TestFindings:
    def run_until_finding(self, engine, max_rounds=6):
        for _ in range(max_rounds):
            result = engine.process(WAVE, PARTICLE)
            if result.findings:
                return result
        return result

    def test_repeated_tension_produces_validated_finding(self, engine):
        result = self.run_until_finding(engine)
        assert result.findings, "stable attractor should yield a finding"
        finding = result.findings[0]
        assert finding.validation_status == "validated"
        assert finding.confidence >= 0.5
        assert "hybrid" in finding.insight
        # Full lineage traceability back to the source paradox.
        paradox_id = result.paradox_nodes[0].paradox_id
        assert paradox_id in finding.lineage
        assert finding.attractor_id in finding.lineage

    def test_finding_emitted_once_per_attractor(self, engine):
        self.run_until_finding(engine)
        result = engine.process(WAVE, PARTICLE)
        assert result.findings == []  # no duplicate findings
        assert len(engine.memory.findings) == 1

    def test_finding_is_queryable_from_memory(self, engine):
        result = self.run_until_finding(engine)
        finding = result.findings[0]
        paradox_id = result.paradox_nodes[0].paradox_id
        assert engine.memory.findings_by_paradox(paradox_id) == [finding]
        assert engine.memory.findings_by_attractor(finding.attractor_id) == [finding]

    def test_export_is_read_only_and_complete(self, engine):
        result = self.run_until_finding(engine)
        finding = result.findings[0]
        from ple.findings import finding_export

        payload = finding_export.export(finding, destination="test_host")
        assert payload["insight"] == finding.insight
        assert payload["validation_status"] == "validated"
        assert payload["lineage"] == list(finding.lineage)
        assert finding.export_metadata["exports"][0]["destination"] == "test_host"


class TestMemoryAndMetrics:
    def test_episodes_accumulate_chronologically(self, engine):
        engine.process(WAVE, PARTICLE)
        engine.process(WAVE, PARTICLE)
        episodes = engine.memory.episodes
        assert len(episodes) == 2
        assert episodes[0].timestamp <= episodes[1].timestamp

    def test_episode_completeness(self, engine):
        result = engine.process(WAVE, PARTICLE)
        ep = result.episode
        assert ep.paradox_ids
        assert ep.synthesis_ids
        assert ep.lattice_snapshot_id
        assert engine.memory.get_snapshot(ep.lattice_snapshot_id) is not None
        sig = ep.tension_signature
        assert sig.paradox_density > 0
        assert sig.coherence_profile

    def test_metrics_present(self, engine):
        result = engine.process(WAVE, PARTICLE)
        assert 0 < result.metrics["paradox_density"] <= 1
        assert result.metrics["tension_load"] > 0
        assert result.metrics["synthesis_quality"] > 0


class TestMultipleContradictionTypes:
    def test_logical_contradiction_takes_coexistence_route(self, engine):
        a = {"name": "optimist", "claims": {"glass_full": True}}
        b = {"name": "pessimist", "claims": {"glass_full": False}}
        result = engine.process(a, b)
        assert result.paradox_nodes[0].contradiction_type == "logical"
        assert result.syntheses[0].method == "coexistence"

    def test_contextual_contradiction(self, engine):
        a = {"name": "newton", "claims": {"gravity": "a force"}}
        b = {"name": "einstein", "claims": {"gravity": "curved spacetime"}}
        ctx = {"frame_domains": {"newton": "classical", "einstein": "relativistic"}}
        result = engine.process(a, b, ctx)
        assert result.paradox_nodes[0].contradiction_type == "contextual"
        assert result.syntheses[0].method == "coexistence"

    def test_independent_paradoxes_coexist_in_one_lattice(self, engine):
        engine.process(WAVE, PARTICLE)
        a = {"name": "optimist", "claims": {"glass_full": True}}
        b = {"name": "pessimist", "claims": {"glass_full": False}}
        result = engine.process(a, b)
        assert len(result.lattice.nodes_of_type("paradox")) == 2
        # The field covers all active paradoxes.
        assert len(result.tension_field.paradox_ids) == 2
