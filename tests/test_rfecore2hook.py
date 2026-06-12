"""RFE-Core2 hook: evaluator telemetry -> frames -> paradox processing.

Contract assertions: the hook is read-only (never mutates the engine or the
frames it built), dormant when all evaluators agree, and its discretization
makes recurring disagreements form attractors and findings.
"""

import copy

import pytest

from ple import ParadoxLatticeEngine
from ple.integration import rfecore2hook
from ple.integration.rfecore2hook import frames_from_cycle, submit_cycle


def make_telemetry(**overrides):
    """A consonant cycle: every evaluator agrees, nothing should fire."""
    telemetry = {
        "watcher_geometric": 0.80,
        "watcher_temporal": 0.82,
        "watcher_resonance": 0.79,
        "coherence_delta": 0.0,
        "valence": 0.0,
        "dominant_emotion": "stability",
        "decision": "allow",
        "manipulation_severity": 0.0,
        "rhythm": "stabilize",
    }
    telemetry.update(overrides)
    return telemetry


@pytest.fixture
def engine():
    return ParadoxLatticeEngine()


class TestFrameConstruction:
    def test_eight_frames_with_designed_claim_keys(self):
        frames = frames_from_cycle(make_telemetry())
        assert len(frames) == 8
        by_name = {f["name"]: f["claims"] for f in frames}
        assert set(by_name["watcher_geometric"]) == {"coherence_band"}
        assert set(by_name["field_delta"]) == {"trajectory_sign"}
        assert set(by_name["emotion"]) == {"trajectory_sign", "posture"}
        assert set(by_name["rhythm_router"]) == {"posture"}
        assert set(by_name["governance"]) == {"threat_level"}
        assert set(by_name["resistance"]) == {"threat_level"}

    def test_missing_keys_raise(self):
        telemetry = make_telemetry()
        del telemetry["valence"]
        with pytest.raises(ValueError, match="valence"):
            frames_from_cycle(telemetry)

    def test_coherence_band_boundaries(self):
        frames = frames_from_cycle(
            make_telemetry(
                watcher_geometric=0.4499,
                watcher_temporal=0.45,
                watcher_resonance=0.75,
            )
        )
        by_name = {f["name"]: f["claims"] for f in frames}
        assert by_name["watcher_geometric"]["coherence_band"] == "low"
        assert by_name["watcher_temporal"]["coherence_band"] == "mid"
        assert by_name["watcher_resonance"]["coherence_band"] == "high"

    def test_trajectory_deadbands(self):
        by_name = {
            f["name"]: f["claims"]
            for f in frames_from_cycle(
                make_telemetry(coherence_delta=0.01, valence=-0.05)
            )
        }
        # Exactly at the deadband is flat; strictly beyond it is signed.
        assert by_name["field_delta"]["trajectory_sign"] == "flat"
        assert by_name["emotion"]["trajectory_sign"] == "flat"
        by_name = {
            f["name"]: f["claims"]
            for f in frames_from_cycle(
                make_telemetry(coherence_delta=0.011, valence=-0.051)
            )
        }
        assert by_name["field_delta"]["trajectory_sign"] == "improving"
        assert by_name["emotion"]["trajectory_sign"] == "degrading"

    def test_severity_threat_bands(self):
        for severity, expected in [(0.29, "none"), (0.30, "elevated"), (0.60, "high")]:
            by_name = {
                f["name"]: f["claims"]
                for f in frames_from_cycle(
                    make_telemetry(manipulation_severity=severity)
                )
            }
            assert by_name["resistance"]["threat_level"] == expected

    def test_governance_threat_mapping(self):
        for decision, expected in [
            ("allow", "none"),
            ("ALLOW", "none"),
            ("monitor", "elevated"),
            ("allow_weakened", "elevated"),
            ("quarantine", "high"),
            ("sacred_shield", "high"),
        ]:
            by_name = {
                f["name"]: f["claims"]
                for f in frames_from_cycle(make_telemetry(decision=decision))
            }
            assert by_name["governance"]["threat_level"] == expected

    def test_posture_mapping(self):
        by_name = {
            f["name"]: f["claims"]
            for f in frames_from_cycle(
                make_telemetry(dominant_emotion="curiosity", rhythm="explore")
            )
        }
        assert by_name["emotion"]["posture"] == "explore"
        assert by_name["rhythm_router"]["posture"] == "explore"
        by_name = {
            f["name"]: f["claims"]
            for f in frames_from_cycle(
                make_telemetry(dominant_emotion="joy", rhythm="dream")
            )
        }
        assert by_name["emotion"]["posture"] == "consolidate"
        assert by_name["rhythm_router"]["posture"] == "consolidate"


class TestDormancy:
    def test_consonant_cycle_stays_dormant(self, engine):
        result = submit_cycle(engine, make_telemetry())
        assert not result.triggered
        assert engine.memory.episodes == ()
        assert engine.memory.get_active_paradoxes() == []


class TestDesignedContradictions:
    def claim_keys(self, result):
        return {n.context_window.get("claim_key") for n in result.paradox_nodes}

    def test_watcher_component_disagreement(self, engine):
        result = submit_cycle(
            engine, make_telemetry(watcher_geometric=0.30)
        )
        assert result.triggered
        assert "coherence_band" in self.claim_keys(result)

    def test_affect_vs_field_trajectory(self, engine):
        result = submit_cycle(
            engine, make_telemetry(coherence_delta=0.05, valence=-0.30)
        )
        assert result.triggered
        assert "trajectory_sign" in self.claim_keys(result)

    def test_governance_vs_resistance(self, engine):
        result = submit_cycle(
            engine, make_telemetry(decision="allow", manipulation_severity=0.70)
        )
        assert result.triggered
        assert "threat_level" in self.claim_keys(result)

    def test_emotion_vs_router_posture(self, engine):
        result = submit_cycle(
            engine, make_telemetry(dominant_emotion="curiosity", rhythm="stabilize")
        )
        assert result.triggered
        assert "posture" in self.claim_keys(result)

    def test_three_watchers_conflicting_nest(self, engine):
        result = submit_cycle(
            engine,
            make_telemetry(
                watcher_geometric=0.30,
                watcher_temporal=0.60,
                watcher_resonance=0.90,
            ),
        )
        band_nodes = [
            n
            for n in result.paradox_nodes
            if n.context_window.get("claim_key") == "coherence_band"
        ]
        assert len(band_nodes) == 3  # all three pairwise contradictions
        nested = [n for n in band_nodes if n.nested_paradox_ids]
        assert len(nested) == 1  # merged under the hottest one
        assert len(nested[0].nested_paradox_ids) == 2


class TestRecurrence:
    def test_recurring_disagreement_forms_attractor_then_finding(self, engine):
        telemetry = make_telemetry(decision="allow", manipulation_severity=0.70)
        submit_cycle(engine, telemetry)
        result = submit_cycle(engine, telemetry)
        assert result.attractors, "second encounter should form an attractor"

        for _ in range(4):
            if result.findings:
                break
            result = submit_cycle(engine, telemetry)
        assert result.findings, "recurring disagreement should yield a finding"
        assert result.findings[0].validation_status == "validated"


class TestReadOnly:
    def test_hook_does_not_mutate_its_frames(self, engine):
        telemetry = make_telemetry(watcher_geometric=0.30)
        frames = frames_from_cycle(telemetry)
        snapshot = copy.deepcopy(frames)
        from ple.integration.external_api import submit_frames

        submit_frames(engine, frames)
        assert frames == snapshot

    def test_hook_does_not_mutate_telemetry(self, engine):
        telemetry = make_telemetry(watcher_geometric=0.30)
        snapshot = dict(telemetry)
        submit_cycle(engine, telemetry)
        assert telemetry == snapshot

    def test_actor_constant_declared(self):
        assert rfecore2hook.ACTOR == "rfecore2hook"

    def test_context_threads_through_to_episode(self, engine):
        context = {"host": "rfe-core2", "cycle": 17, "arm": "control"}
        result = submit_cycle(
            engine, make_telemetry(watcher_geometric=0.30), context
        )
        assert result.episode.context_window == context
