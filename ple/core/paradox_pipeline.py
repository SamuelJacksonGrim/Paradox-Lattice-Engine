"""The paradox pipeline — PLE's core execution path (paradox_pipeline.md).

Contradiction Detected
        -> Paradox Detector -> ParadoxNode
        -> Tension Field Generation
        -> Paradox Lattice Construction / Update
        -> Synthesis Engine Pass
        -> Attractor Dynamics (recurrence -> stability)
        -> Finding Extraction (from stable attractors)
        -> Memory Encoding (Paradox Episode)
        -> Metrics & Events

The engine is stateful across runs: recurrence of similar syntheses over
repeated encounters with the same contradiction is what forms attractors and
eventually findings. PLE runs only when contradictions appear.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ple import events
from ple.attractors import (
    attractor_evolution,
    attractor_stability,
)
from ple.attractors.attractor_detector import AttractorDetector
from ple.attractors.attractor_registry import AttractorRegistry
from ple.core.tension_router import TensionRouter
from ple.fields import resolution_horizon, tension_field_generator
from ple.findings import finding_extractor, finding_validator
from ple.lattice import lattice_builder, lattice_simplifier
from ple.memory.paradox_memory_buffer import ParadoxMemoryBuffer
from ple.metrics import ecology
from ple.models.attractor import Attractor, AttractorState
from ple.models.finding import Finding
from ple.models.lattice import ParadoxLattice
from ple.models.paradox import ParadoxNode
from ple.models.synthesis import SynthesisRecord
from ple.models.tension_field import TensionField
from ple.paradox import (
    contradiction_classifier,
    paradox_detector,
    paradox_intensity_model,
    paradox_normalizer,
)
from ple.synthesis import synthesis_engine


@dataclass
class PipelineResult:
    """Output of one pipeline run (one contradiction encounter)."""

    paradox_nodes: list[ParadoxNode] = field(default_factory=list)
    tension_field: TensionField | None = None
    lattice: ParadoxLattice | None = None
    syntheses: list[SynthesisRecord] = field(default_factory=list)
    attractors: list[Attractor] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)
    episode = None
    metrics: dict = field(default_factory=dict)

    @property
    def triggered(self) -> bool:
        """PLE activates only when contradictions appear."""
        return bool(self.paradox_nodes)


class ParadoxLatticeEngine:
    """Stateful orchestrator — owns the lattice, memory, registries, and router."""

    def __init__(self) -> None:
        self.router = TensionRouter()
        self.memory = ParadoxMemoryBuffer()
        self.lattice = lattice_builder.initialize()
        self.attractor_registry = AttractorRegistry()
        self.attractor_detector = AttractorDetector(self.attractor_registry)
        self._known_paradoxes: dict[tuple, ParadoxNode] = {}
        self._findings_emitted: set[str] = set()

    # ------------------------------------------------------------------
    def process(
        self, frame_a: dict, frame_b: dict, context: dict | None = None
    ) -> PipelineResult:
        """Run the full pipeline on a pair of frames."""
        context = context or {}
        result = PipelineResult()

        # Stage 1 — paradox detection & normalization
        result.paradox_nodes = self._paradox_stage(frame_a, frame_b, context)
        if not result.triggered:
            return result  # no contradiction, PLE stays dormant

        # Stage 2 — tension field generation
        result.tension_field = self._tension_stage(context)

        # Stage 3 — lattice construction / update
        result.lattice = self._lattice_stage(
            result.paradox_nodes, result.tension_field
        )

        # Stage 4 — synthesis pass + attractor dynamics + findings
        result.syntheses = self._synthesis_stage(
            result.paradox_nodes, result.tension_field
        )
        result.attractors, result.findings = self._attractor_stage(
            result.paradox_nodes, result.syntheses
        )

        # Stage 5 — memory & metrics
        result.episode = self._memory_stage(result, context)
        result.metrics = {
            "paradox_density": ecology.paradox_density(self.lattice),
            "tension_load": ecology.tension_load(result.tension_field),
            "synthesis_quality": ecology.synthesis_quality(result.syntheses),
            "stability": ecology.stability_profile(self.lattice),
        }
        return result

    # -- Stage 1 ---------------------------------------------------------
    def _paradox_stage(
        self, frame_a: dict, frame_b: dict, context: dict
    ) -> list[ParadoxNode]:
        nodes: list[ParadoxNode] = []
        for raw in paradox_detector.detect(frame_a, frame_b, context):
            ctype = contradiction_classifier.classify(raw, context)
            intensity = paradox_intensity_model.estimate(raw, ctype, context)

            sig = (frozenset({raw.frame_a, raw.frame_b}), raw.claim_key, ctype)
            known = self._known_paradoxes.get(sig)
            if known is not None:
                # Re-encounter: the contradiction sharpens; re-intensify.
                paradox_intensity_model.intensify(known, 0.1)
                self.router.emit(
                    events.ParadoxEvent(
                        event_type="updated", paradox_id=known.paradox_id
                    )
                )
                nodes.append(known)
                continue

            node = paradox_normalizer.to_paradox_node(raw, ctype, intensity, context)
            self._known_paradoxes[sig] = node
            self.memory.track_paradox(node)
            self.router.emit(
                events.ParadoxEvent(event_type="detected", paradox_id=node.paradox_id)
            )
            self.router.emit(
                events.ParadoxEvent(
                    event_type="normalized", paradox_id=node.paradox_id
                )
            )
            nodes.append(node)
        return nodes

    # -- Stage 2 ---------------------------------------------------------
    def _tension_stage(self, context: dict) -> TensionField:
        active = self.memory.get_active_paradoxes()
        field_obj = tension_field_generator.build(active, context)
        resolution_horizon.update_from_field(field_obj, active)
        self.router.emit(
            events.TensionFieldEvent(
                event_type="generated", field_id=field_obj.field_id
            )
        )
        return field_obj

    # -- Stage 3 ---------------------------------------------------------
    def _lattice_stage(
        self, paradoxes: list[ParadoxNode], field_obj: TensionField
    ) -> ParadoxLattice:
        for node in paradoxes:
            lattice_builder.update_with_paradox(self.lattice, node, field_obj)
            self.router.emit(
                events.LatticeUpdateEvent(
                    event_type="node_added", lattice_id=self.lattice.lattice_id
                )
            )
        lattice_simplifier.simplify(self.lattice)
        return self.lattice

    # -- Stage 4 ---------------------------------------------------------
    def _synthesis_stage(
        self, paradoxes: list[ParadoxNode], field_obj: TensionField
    ) -> list[SynthesisRecord]:
        records: list[SynthesisRecord] = []
        candidates = synthesis_engine.find_candidates(
            self.lattice, field_obj, paradoxes
        )
        for paradox in candidates:
            record = synthesis_engine.synthesize(paradox, self.lattice, field_obj)
            records.append(record)
            self.router.emit(
                events.SynthesisEvent(
                    event_type="created", synthesis_id=record.synthesis_id
                )
            )
        return records

    def _attractor_stage(
        self,
        paradoxes: list[ParadoxNode],
        records: list[SynthesisRecord],
    ) -> tuple[list[Attractor], list[Finding]]:
        attractors: list[Attractor] = []
        findings: list[Finding] = []
        by_id = {p.paradox_id: p for p in paradoxes}

        for record in records:
            paradox = by_id[record.paradox_ids[0]]
            sig = paradox_normalizer.signature(paradox)
            attractor = self.attractor_detector.observe(sig, record)
            if attractor is None:
                continue

            if attractor.state == AttractorState.FORMING:
                attractor_evolution.activate(attractor, self.lattice)
                self.router.emit(
                    events.AttractorEvent(
                        event_type="activated", attractor_id=attractor.attractor_id
                    )
                )
            elif attractor.state in (
                AttractorState.ACTIVE,
                AttractorState.STABILIZING,
            ):
                attractor_evolution.record_recurrence(
                    attractor, record.synthesis_id
                )

            count = self.attractor_detector.recurrence_count(sig, record.method)
            attractor_stability.reinforce(attractor, count)
            attractors.append(attractor)

            finding = self._maybe_extract_finding(attractor, paradox)
            if finding is not None:
                findings.append(finding)
        return attractors, findings

    def _maybe_extract_finding(
        self, attractor: Attractor, paradox: ParadoxNode
    ) -> Finding | None:
        if attractor.attractor_id in self._findings_emitted:
            return None
        if attractor.stability_score < finding_extractor.MIN_STABILITY:
            return None
        finding = finding_extractor.extract(
            attractor,
            source_paradox_ids=[paradox.paradox_id],
            claim=paradox.context_window.get("claim_key", "claim"),
            frames=sorted(paradox.frames),
        )
        finding_validator.validate(finding, self.attractor_registry)
        self.memory.store_finding(finding)
        self._findings_emitted.add(attractor.attractor_id)
        self.router.emit(
            events.FindingEvent(
                event_type="finding_created", finding_id=finding.finding_id
            )
        )
        return finding

    # -- Stage 5 ---------------------------------------------------------
    def _memory_stage(self, result: PipelineResult, context: dict):
        resolution_state = "unresolved"
        if result.findings:
            resolution_state = "partial"  # tension reorganized, paradox intact
        episode = self.memory.store_episode(
            paradox_ids=[p.paradox_id for p in result.paradox_nodes],
            field=result.tension_field,
            lattice_snapshot=self.lattice.snapshot(),
            synthesis_records=result.syntheses,
            attractor_ids=[a.attractor_id for a in result.attractors],
            finding_ids=[f.finding_id for f in result.findings],
            resolution_state=resolution_state,
            context=context,
        )
        self.router.emit(
            events.MemoryEvent(
                event_type="episode_created", object_id=episode.episode_id
            )
        )
        return episode
