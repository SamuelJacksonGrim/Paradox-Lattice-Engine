"""Phase 2-6 behaviors: collapse prediction, lattice patterns, multi-frame
merging, anti-ossification, flooding guards, and the integration facade.
"""

import pytest

from ple import ParadoxLatticeEngine
from ple.events import ResolutionEvent
from ple.integration import external_api, system_hooks
from ple.models.attractor import AttractorState
from ple.models.paradox import ParadoxState

WAVE = {"name": "wave_theory", "claims": {"light_is": "a wave"}}
PARTICLE = {"name": "particle_theory", "claims": {"light_is": "a particle"}}
FIELD = {"name": "field_theory", "claims": {"light_is": "a field excitation"}}


@pytest.fixture
def engine():
    return ParadoxLatticeEngine()


class TestCollapsePrediction:
    def test_horizons_emitted_each_run(self, engine):
        result = engine.process(WAVE, PARTICLE)
        assert len(result.horizons) == 1
        horizon = result.horizons[0]
        assert 0.0 <= horizon.collapse_probability <= 1.0
        assert result.paradox_nodes[0].paradox_id in horizon.paradox_ids
        # Horizons are recorded on the lattice.
        assert horizon.horizon_id in result.lattice.resolution_horizons

    def test_collapse_probability_rises_as_tension_drains(self, engine):
        r1 = engine.process(WAVE, PARTICLE)
        p1 = r1.horizons[0].collapse_probability
        r2 = engine.process(WAVE, PARTICLE)
        for _ in range(4):
            r2 = engine.process(WAVE, PARTICLE)
        assert r2.horizons[0].collapse_probability > p1

    def test_fully_drained_paradox_collapses_to_attenuated(self, engine):
        # Repeated synthesis drains tension; eventually intensity < 0.05
        # and the paradox attenuates (never resolves, never deletes).
        node = None
        for _ in range(30):
            r = engine.process(WAVE, PARTICLE)
            node = r.paradox_nodes[0]
            if node.state == ParadoxState.ATTENUATED:
                break
        assert node.state == ParadoxState.ATTENUATED
        # Still queryable, still in the lattice, still in the ecology.
        assert engine.memory.get_paradox(node.paradox_id) is node
        assert engine.lattice.find_paradox_node(node.paradox_id) is not None
        # A 'collapsed' ResolutionEvent was emitted; never 'resolved'/'deleted'.
        outcomes = {e.event_type for e in engine.router.events_of(ResolutionEvent)}
        assert "collapsed" in outcomes

    def test_attenuated_paradox_flares_back_on_reencounter(self, engine):
        for _ in range(30):
            r = engine.process(WAVE, PARTICLE)
            if r.paradox_nodes[0].state == ParadoxState.ATTENUATED:
                break
        r = engine.process(WAVE, PARTICLE)  # the contradiction returns
        assert r.paradox_nodes[0].state == ParadoxState.ACTIVE
        assert r.paradox_nodes[0].intensity > 0


class TestLatticePatternStore:
    def test_recurring_shapes_are_clustered(self, engine):
        engine.process(WAVE, PARTICLE)
        snap1 = engine.memory.episodes[0].lattice_snapshot_id
        # Same contradiction, same structural shape after attractor forms?
        # The shape changes as nodes are added, so distinct signatures appear;
        # but identical consecutive runs (post-stabilization) recur.
        for _ in range(4):
            engine.process(WAVE, PARTICLE)
        patterns = engine.pattern_store.patterns()
        assert patterns, "patterns recorded for every episode"
        total = sum(p.recurrence for p in patterns)
        assert total == len(engine.memory.episodes)

    def test_stable_ecology_produces_recurring_pattern(self, engine):
        for _ in range(5):
            engine.process(WAVE, PARTICLE)
        recurring = engine.pattern_store.patterns(min_recurrence=2)
        assert recurring, "a settled lattice shape should recur"

    def test_signature_counts_synthesis_chains(self, engine):
        engine.process(WAVE, PARTICLE)
        engine.process(WAVE, PARTICLE)  # attractor forms
        snapshot = engine.lattice.snapshot()
        from ple.memory.lattice_pattern_store import signature_of

        sig = signature_of(snapshot)
        label, chains = sig[2]
        assert label == "paradox_synthesis_attractor_chains"
        assert chains >= 1


class TestMultiFrame:
    def test_three_frames_produce_three_pairwise_paradoxes(self, engine):
        result = engine.process_many([WAVE, PARTICLE, FIELD])
        assert len(result.paradox_nodes) == 3

    def test_cross_frame_merging_nests_under_hottest(self, engine):
        result = engine.process_many([WAVE, PARTICLE, FIELD])
        parents = [p for p in result.paradox_nodes if p.nested_paradox_ids]
        assert len(parents) == 1
        parent = parents[0]
        assert len(parent.nested_paradox_ids) == 2
        # Nesting is recorded in lineage, children remain intact paradoxes.
        assert any(e.startswith("nested:") for e in parent.lineage)
        for child_id in parent.nested_paradox_ids:
            child = engine.memory.get_paradox(child_id)
            assert child.state == ParadoxState.ACTIVE

    def test_multi_frame_still_reaches_findings(self, engine):
        engine.process_many([WAVE, PARTICLE, FIELD])
        result = engine.process_many([WAVE, PARTICLE, FIELD])
        assert result.findings, "recurrence across the trio yields findings"

    def test_two_frames_via_process_many_equals_process(self, engine):
        result = engine.process_many([WAVE, PARTICLE])
        assert len(result.paradox_nodes) == 1
        assert not result.paradox_nodes[0].nested_paradox_ids


class TestAntiOssification:
    def test_new_paradox_on_shared_frame_shakes_attractor(self, engine):
        # Build a stable attractor on wave/particle.
        engine.process(WAVE, PARTICLE)
        r = engine.process(WAVE, PARTICLE)
        attractor = r.attractors[0]
        before = attractor.stability_score

        # A brand-new contradiction involving wave_theory arrives.
        challenger = {"name": "wave_theory", "claims": {"medium": "aether"}}
        rival = {"name": "relativity", "claims": {"medium": "none"}}
        engine.process(challenger, rival)

        assert attractor.stability_score < before

    def test_unrelated_paradox_does_not_shake_attractor(self, engine):
        engine.process(WAVE, PARTICLE)
        r = engine.process(WAVE, PARTICLE)
        attractor = r.attractors[0]
        before = attractor.stability_score

        a = {"name": "optimist", "claims": {"glass_full": True}}
        b = {"name": "pessimist", "claims": {"glass_full": False}}
        engine.process(a, b)

        assert attractor.stability_score == before


class TestFloodingGuard:
    def test_overflow_archives_drained_attenuated_paradoxes(self):
        engine = ParadoxLatticeEngine(max_active_paradoxes=3)
        # Drain one paradox to attenuation first.
        for _ in range(30):
            r = engine.process(WAVE, PARTICLE)
            if r.paradox_nodes[0].state == ParadoxState.ATTENUATED:
                break
        drained = r.paradox_nodes[0]
        assert drained.state == ParadoxState.ATTENUATED

        # Now flood with fresh unrelated paradoxes past the cap.
        for i in range(4):
            a = {"name": f"claim_{i}_yes", "claims": {f"q{i}": True}}
            b = {"name": f"claim_{i}_no", "claims": {f"q{i}": False}}
            engine.process(a, b)

        assert drained.state == ParadoxState.ARCHIVED
        # Archived paradoxes remain queryable forever.
        assert engine.memory.get_paradox(drained.paradox_id) is drained
        # Active, hot paradoxes were never archived prematurely.
        for p in engine.memory.get_active_paradoxes():
            assert p.state != ParadoxState.ARCHIVED


class TestIntegration:
    def test_submit_frames_dispatches_by_arity(self, engine):
        r2 = external_api.submit_frames(engine, [WAVE, PARTICLE])
        assert len(r2.paradox_nodes) == 1
        r3 = external_api.submit_frames(engine, [WAVE, PARTICLE, FIELD])
        assert len(r3.paradox_nodes) == 3
        with pytest.raises(ValueError):
            external_api.submit_frames(engine, [WAVE])

    def test_get_findings_exports_validated_only(self, engine):
        engine.process(WAVE, PARTICLE)
        engine.process(WAVE, PARTICLE)
        exported = external_api.get_findings(engine)
        assert len(exported) == 1
        assert exported[0]["validation_status"] == "validated"
        assert exported[0]["insight"]

    def test_ecology_report_observability(self, engine):
        engine.process(WAVE, PARTICLE)
        engine.process(WAVE, PARTICLE)
        report = external_api.ecology_report(engine)
        assert report["active_paradoxes"] == 1
        assert report["findings"] == 1
        assert report["episodes"] == 2
        assert report["lattice_nodes"] > 0
        assert len(report["attractors"]) == 1
        assert report["events_routed"] > 0

    def test_hooks_receive_events(self, engine):
        seen = []
        system_hooks.register(engine, "finding", seen.append)
        engine.process(WAVE, PARTICLE)
        assert seen == []  # no finding on first encounter
        engine.process(WAVE, PARTICLE)
        assert len(seen) == 1
        assert seen[0].event_type == "finding_created"

    def test_unknown_hook_channel_rejected(self, engine):
        with pytest.raises(ValueError):
            system_hooks.register(engine, "vibes", print)

    def test_lae_transition_trigger_fires_on_tension(self, engine):
        triggers = []
        system_hooks.register_transition_trigger(engine, triggers.append)
        engine.process(WAVE, PARTICLE)
        assert triggers, "tension generation should fire transition triggers"
