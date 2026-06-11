"""The paradox pipeline — PLE's core execution path (paradox_pipeline.md).

Contradiction Detected
        -> Paradox Detector -> ParadoxNode
        -> Tension Field Generation
        -> Paradox Lattice Construction / Update
        -> Synthesis Engine Pass
        -> Attractor Dynamics (recurrence -> stability)
        -> Resolution Horizons (collapse prediction)
        -> Finding Extraction (from stable attractors)
        -> Memory Encoding (Paradox Episode + lattice patterns)
        -> Metrics & Events

The engine is stateful across runs: recurrence of similar syntheses over
repeated encounters with the same contradiction is what forms attractors and
eventually findings. PLE runs only when contradictions appear.

Failure-mode guards (ARCHITECTURE.md §10):
- paradox flooding   -> density cap archives drained, attenuated paradoxes
- stability ossification -> new paradoxes touching an attractor's frames
  destabilize it, so settled structure stays answerable to fresh tension
- premature collapse -> collapse is only confirmed when tension has actually
  drained below the threshold, never forced
"""

from __future__ import annotations

from itertools import combinations
from dataclasses import dataclass, field

from ple import events
from ple.attractors import (
    attractor_evolution,
    attractor_stability,
)
from ple.attractors.attractor_detector import AttractorDetector
from ple.attractors.attractor_registry import AttractorRegistry
from ple.core.tension_router import TensionRouter
from ple.fields import tension_field_generator
from ple.findings import finding_extractor, finding_validator
from ple.lattice import lattice_builder, lattice_simplifier
from ple.memory.lattice_pattern_store import LatticePatternStore
from ple.memory.paradox_memory_buffer import ParadoxMemoryBuffer
from ple.metrics import ecology
from ple.models.attractor import Attractor, AttractorState
from ple.models.finding import Finding
from ple.models.horizon import ResolutionHorizon
from ple.models.lattice import ParadoxLattice
from ple.models.paradox import ParadoxNode, ParadoxState
from ple.models.synthesis import SynthesisRecord
from ple.models.tension_field import TensionField
from ple.paradox import (
    contradiction_classifier,
    paradox_detector,
    paradox_intensity_model,
    paradox_normalizer,
)
from ple.synthesis import synthesis_engine
from ple.synthesis.tension_collapse_predictor import (
    TensionCollapsePredictor,
    confirm_collapse,
)


@dataclass
class PipelineResult:
    """Output of one pipeline run (one contradiction encounter)."""

    paradox_nodes: list[ParadoxNode] = field(default_factory=list)
    tension_field: TensionField | None = None
    lattice: ParadoxLattice | None = None
    syntheses: list[SynthesisRecord] = field(default_factory=list)
    attractors: list[Attractor] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)
    horizons: list[ResolutionHorizon] = field(default_factory=list)
    episode = None
    metrics: dict = field(default_factory=dict)

    @property
    def triggered(self) -> bool:
        """PLE activates only when contradictions appear."""
        return bool(self.paradox_nodes)


class ParadoxLatticeEngine:
    """Stateful orchestrator — owns the lattice, memory, registries, and router."""

    def __init__(self, max_active_paradoxes: int = 64) -> None:
        self.router = TensionRouter()
        self.memory = ParadoxMemoryBuffer()
        self.lattice = lattice_builder.initialize()
        self.attractor_registry = AttractorRegistry()
        self.attractor_detector = AttractorDetector(self.attractor_registry)
        self.collapse_predictor = TensionCollapsePredictor()
        self.pattern_store = LatticePatternStore()
        self.max_active_paradoxes = max_active_paradoxes
        self._known_paradoxes: dict[tuple, ParadoxNode] = {}
        self._encounters: dict[tuple, int] = {}
        self._findings_emitted: set[str] = set()

    # ------------------------------------------------------------------
    def process(
        self, frame_a: dict, frame_b: dict, context: dict | None = None
    ) -> PipelineResult:
        """Run the full pipeline on a pair of frames."""
        return self._run([(frame_a, frame_b)], context or {})

    def process_many(
        self, frames: list[dict], context: dict | None = None
    ) -> PipelineResult:
        """Multi-agent / multi-frame entry point: every pair of frames is
        checked for contradiction, and when three or more frames conflict on
        the same claim, the pairwise paradoxes merge into a nested cluster
        under the hottest one (cross-frame paradox merging)."""
        return self._run(list(combinations(frames, 2)), context or {})

    # ------------------------------------------------------------------
    def _run(
        self, pairs: list[tuple[dict, dict]], context: dict
    ) -> PipelineResult:
        result = PipelineResult()

        # Stage 1 — paradox detection & normalization (+ cross-frame merge)
        result.paradox_nodes = self._paradox_stage(pairs, context)
        if not result.triggered:
            return result  # no contradiction, PLE stays dormant
        self._merge_cross_frame(result.paradox_nodes)
        self._guard_paradox_flooding()

        # Stage 2 — tension field generation
        result.tension_field = self._tension_stage(context)

        # Stage 3 — lattice construction / update
        result.lattice = self._lattice_stage(
            result.paradox_nodes, result.tension_field
        )

        # Stage 4 — synthesis pass + attractor dynamics + horizons + findings
        result.syntheses = self._synthesis_stage(
            result.paradox_nodes, result.tension_field
        )
        result.attractors, result.findings = self._attractor_stage(
            result.paradox_nodes, result.syntheses
        )
        result.horizons = self._resolution_stage(result.paradox_nodes)

        # Stage 5 — memory & metrics
        result.episode = self._memory_stage(result, context)
        result.metrics = {
            "paradox_density": ecology.paradox_density(self.lattice),
            "tension_load": ecology.tension_load(result.tension_field),
            "synthesis_quality": ecology.synthesis_quality(result.syntheses),
            "stability": ecology.stability_profile(self.lattice),
            "active_paradoxes": len(self.memory.get_active_paradoxes()),
        }
        return result

    # -- Stage 1 ---------------------------------------------------------
    def _paradox_stage(
        self, pairs: list[tuple[dict, dict]], context: dict
    ) -> list[ParadoxNode]:
        nodes: list[ParadoxNode] = []
        seen_ids: set[str] = set()
        for frame_a, frame_b in pairs:
            for raw in paradox_detector.detect(frame_a, frame_b, context):
                ctype = contradiction_classifier.classify(raw, context)
                intensity = paradox_intensity_model.estimate(raw, ctype, context)

                sig = (frozenset({raw.frame_a, raw.frame_b}), raw.claim_key, ctype)
                self._encounters[sig] = self._encounters.get(sig, 0) + 1
                known = self._known_paradoxes.get(sig)
                if known is not None:
                    if known.paradox_id in seen_ids:
                        continue
                    # Re-encounter: the contradiction sharpens; re-intensify.
                    # Habituation: a contradiction the system has synthesized
                    # many times sharpens less each return, so its tension can
                    # eventually drain past the collapse horizon instead of
                    # oscillating forever. But a collapsed paradox returning
                    # is evidence it was never truly drained — the flare-back
                    # resets habituation and the paradox burns hot again.
                    if known.state == ParadoxState.ATTENUATED:
                        known.transition(
                            ParadoxState.ACTIVE, actor="paradox_layer"
                        )
                        self._encounters[sig] = 1
                    paradox_intensity_model.intensify(
                        known, 0.1 / self._encounters[sig]
                    )
                    self.router.emit(
                        events.ParadoxEvent(
                            event_type="updated", paradox_id=known.paradox_id
                        )
                    )
                    nodes.append(known)
                    seen_ids.add(known.paradox_id)
                    continue

                node = paradox_normalizer.to_paradox_node(
                    raw, ctype, intensity, context
                )
                self._known_paradoxes[sig] = node
                self.memory.track_paradox(node)
                self._destabilize_touched_attractors(node)
                self.router.emit(
                    events.ParadoxEvent(
                        event_type="detected", paradox_id=node.paradox_id
                    )
                )
                self.router.emit(
                    events.ParadoxEvent(
                        event_type="normalized", paradox_id=node.paradox_id
                    )
                )
                nodes.append(node)
                seen_ids.add(node.paradox_id)
        return nodes

    def _merge_cross_frame(self, nodes: list[ParadoxNode]) -> None:
        """When >= 3 frames conflict on the same claim in one run, nest the
        pairwise paradoxes under the most intense one."""
        by_claim: dict[str, list[ParadoxNode]] = {}
        for node in nodes:
            key = node.context_window.get("claim_key")
            by_claim.setdefault(key, []).append(node)

        for cluster in by_claim.values():
            if len(cluster) < 2:
                continue
            frames = set()
            for n in cluster:
                frames |= n.frames
            if len(frames) < 3:
                continue
            parent = max(cluster, key=lambda n: n.intensity)
            for child in cluster:
                if child is parent:
                    continue
                paradox_normalizer.nest(parent, child)
                self.router.emit(
                    events.ParadoxEvent(
                        event_type="nested", paradox_id=child.paradox_id,
                        metadata={"parent": parent.paradox_id},
                    )
                )

    def _destabilize_touched_attractors(self, new_paradox: ParadoxNode) -> None:
        """Anti-ossification: a genuinely new paradox involving an existing
        attractor's frames shakes that attractor's stability, and its
        findings are revalidated against the shaken structure."""
        for (paradox_sig, _method), attractor in self.attractor_registry.items():
            if attractor.state not in (
                AttractorState.ACTIVE,
                AttractorState.STABILIZING,
            ):
                continue
            attractor_frames = paradox_sig[0]
            same_pattern = (
                paradox_sig[0] == frozenset(new_paradox.frames)
                and paradox_sig[1] == new_paradox.context_window.get("claim_key")
            )
            if same_pattern or not (attractor_frames & new_paradox.frames):
                continue
            shock = 0.2 * new_paradox.intensity
            attractor_stability.destabilize(attractor, shock)
            if attractor.state == AttractorState.ATTENUATED:
                self.router.emit(
                    events.AttractorEvent(
                        event_type="attenuated",
                        attractor_id=attractor.attractor_id,
                    )
                )
            for finding in self.memory.findings_by_attractor(
                attractor.attractor_id
            ):
                finding_validator.validate(finding, self.attractor_registry)

    def _guard_paradox_flooding(self) -> None:
        """Density threshold: when the active ecology overflows, the most
        drained attenuated paradoxes are archived (memory's prerogative).
        Active paradoxes are never archived prematurely."""
        active = self.memory.get_active_paradoxes()
        overflow = len(active) - self.max_active_paradoxes
        if overflow <= 0:
            return
        attenuated = sorted(
            (p for p in active if p.state == ParadoxState.ATTENUATED),
            key=lambda p: p.intensity,
        )
        for paradox in attenuated[:overflow]:
            self.memory.archive_paradox(paradox)
            self.router.emit(
                events.ParadoxEvent(
                    event_type="archived", paradox_id=paradox.paradox_id
                )
            )

    # -- Stage 2 ---------------------------------------------------------
    def _tension_stage(self, context: dict) -> TensionField:
        active = self.memory.get_active_paradoxes()
        field_obj = tension_field_generator.build(active, context)
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

            if attractor.state != AttractorState.ATTENUATED:
                count = self.attractor_detector.recurrence_count(
                    sig, record.method
                )
                attractor_stability.reinforce(attractor, count)
            attractors.append(attractor)

            finding = self._maybe_extract_finding(attractor, paradox)
            if finding is not None:
                findings.append(finding)
        return attractors, findings

    def _resolution_stage(
        self, paradoxes: list[ParadoxNode]
    ) -> list[ResolutionHorizon]:
        """Collapse prediction: track post-synthesis intensities, classify
        each paradox's trajectory, and confirm collapses whose tension has
        fully drained."""
        for paradox in paradoxes:
            self.collapse_predictor.observe(paradox)
        horizons = self.collapse_predictor.predict(paradoxes)
        lattice_builder.set_resolution_horizons(
            self.lattice, [h.horizon_id for h in horizons]
        )
        for paradox, horizon in zip(paradoxes, horizons):
            outcome = self.collapse_predictor.classify(paradox)
            if outcome == "collapsed":
                confirm_collapse(paradox)
            self.router.emit(
                events.ResolutionEvent(
                    event_type=outcome, horizon_id=horizon.horizon_id
                )
            )
        return horizons

    def _maybe_extract_finding(
        self, attractor: Attractor, paradox: ParadoxNode
    ) -> Finding | None:
        if attractor.attractor_id in self._findings_emitted:
            return None
        if attractor.state in (
            AttractorState.ATTENUATED,
            AttractorState.CANDIDATE,
            AttractorState.FORMING,
        ):
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
        if any(
            p.state == ParadoxState.ATTENUATED for p in result.paradox_nodes
        ):
            resolution_state = "collapsed"
        elif result.findings:
            resolution_state = "partial"  # tension reorganized, paradox intact
        snapshot = self.lattice.snapshot()
        self.pattern_store.record(snapshot)
        episode = self.memory.store_episode(
            paradox_ids=[p.paradox_id for p in result.paradox_nodes],
            field=result.tension_field,
            lattice_snapshot=snapshot,
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
