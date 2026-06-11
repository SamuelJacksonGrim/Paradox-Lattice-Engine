"""Stage 1: detection, classification, intensity, normalization."""

import pytest

from ple.errors import InvalidLifecycleTransition, InvalidParadox, UnauthorizedMutation
from ple.models.paradox import ParadoxNode, ParadoxState
from ple.paradox import (
    contradiction_classifier,
    paradox_detector,
    paradox_intensity_model,
    paradox_normalizer,
)


def frames(va, vb, key="claim"):
    return (
        {"name": "frame_a", "claims": {key: va}},
        {"name": "frame_b", "claims": {key: vb}},
    )


class TestDetection:
    def test_detects_conflicting_claims(self):
        a, b = frames("blue", "red", key="sky_color")
        found = paradox_detector.detect(a, b)
        assert len(found) == 1
        assert found[0].claim_key == "sky_color"

    def test_no_contradiction_no_detection(self):
        a, b = frames("blue", "blue")
        assert paradox_detector.detect(a, b) == []

    def test_triviality_filter_rephrasing_is_not_paradox(self):
        # Persistence under normalization: case/whitespace rephrasings vanish.
        a, b = frames("The  Sky is BLUE", "the sky is blue")
        assert paradox_detector.detect(a, b) == []

    def test_disjoint_claims_are_not_contradictions(self):
        a = {"name": "frame_a", "claims": {"x": 1}}
        b = {"name": "frame_b", "claims": {"y": 2}}
        assert paradox_detector.detect(a, b) == []


class TestClassification:
    def test_opposed_booleans_are_logical(self):
        a, b = frames(True, False)
        raw = paradox_detector.detect(a, b)[0]
        assert contradiction_classifier.classify(raw) == "logical"

    def test_different_strings_are_semantic(self):
        a, b = frames("wave", "particle")
        raw = paradox_detector.detect(a, b)[0]
        assert contradiction_classifier.classify(raw) == "semantic"

    def test_domain_scoped_frames_are_contextual(self):
        a, b = frames("wave", "particle")
        ctx = {"frame_domains": {"frame_a": "optics", "frame_b": "quantum"}}
        raw = paradox_detector.detect(a, b, ctx)[0]
        assert contradiction_classifier.classify(raw, ctx) == "contextual"

    def test_self_reference_is_self_referential(self):
        a, b = frames("this frame_a statement is false", "it is true")
        raw = paradox_detector.detect(a, b)[0]
        assert contradiction_classifier.classify(raw) == "self_referential"


class TestParadoxNode:
    def test_normalizer_walks_lifecycle_to_active(self):
        a, b = frames("wave", "particle")
        raw = paradox_detector.detect(a, b)[0]
        node = paradox_normalizer.to_paradox_node(raw, "semantic", 0.6)
        assert node.state == ParadoxState.ACTIVE
        assert node.lineage  # lineage starts at detection

    def test_identical_frames_rejected(self):
        with pytest.raises(InvalidParadox):
            ParadoxNode(
                frame_a="same", frame_b="same",
                contradiction_type="semantic", intensity=0.5,
            )

    def test_unknown_contradiction_type_rejected(self):
        with pytest.raises(InvalidParadox):
            ParadoxNode(
                frame_a="a", frame_b="b",
                contradiction_type="vibes", intensity=0.5,
            )

    def test_intensity_bounds_enforced(self):
        with pytest.raises(InvalidParadox):
            ParadoxNode(
                frame_a="a", frame_b="b",
                contradiction_type="semantic", intensity=1.5,
            )


class TestIntensityContract:
    def make_node(self):
        return ParadoxNode(
            frame_a="a", frame_b="b",
            contradiction_type="semantic", intensity=0.5,
        )

    def test_only_intensity_model_may_mutate_intensity(self):
        node = self.make_node()
        with pytest.raises(Exception):
            node.intensity = 0.9  # frozen dataclass

    def test_intensity_model_updates_are_clamped(self):
        node = self.make_node()
        paradox_intensity_model.intensify(node, 5.0)
        assert node.intensity == 1.0
        paradox_intensity_model.attenuate(node, 1.0)
        assert node.intensity == 0.0

    def test_contradiction_type_is_immutable(self):
        node = self.make_node()
        with pytest.raises(Exception):
            node.contradiction_type = "logical"

    def test_unauthorized_actor_cannot_use_gateway(self):
        from ple.models._mutation import authorized_set

        node = self.make_node()
        with pytest.raises(UnauthorizedMutation):
            authorized_set(node, "intensity", 0.1, actor="synthesis_engine")
        with pytest.raises(UnauthorizedMutation):
            authorized_set(node, "frame_a", "x", actor="paradox_intensity_model")


class TestLifecycle:
    def make_active(self):
        a, b = frames("wave", "particle")
        raw = paradox_detector.detect(a, b)[0]
        return paradox_normalizer.to_paradox_node(raw, "semantic", 0.6)

    def test_only_synthesis_or_attractor_may_attenuate(self):
        node = self.make_active()
        with pytest.raises(InvalidLifecycleTransition):
            node.transition(ParadoxState.ATTENUATED, actor="paradox_layer")
        node.transition(ParadoxState.ATTENUATED, actor="synthesis_engine")
        assert node.state == ParadoxState.ATTENUATED

    def test_only_memory_may_archive(self):
        node = self.make_active()
        with pytest.raises(InvalidLifecycleTransition):
            node.transition(ParadoxState.ARCHIVED, actor="synthesis_engine")
        node.transition(ParadoxState.ARCHIVED, actor="memory")
        assert node.state == ParadoxState.ARCHIVED

    def test_no_resolution_transition_exists(self):
        node = self.make_active()
        # Paradoxes can never go back to 'detected' or skip states arbitrarily.
        with pytest.raises(InvalidLifecycleTransition):
            node.transition(ParadoxState.DETECTED, actor="paradox_layer")
