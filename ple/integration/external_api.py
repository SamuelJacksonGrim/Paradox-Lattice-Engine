"""External API — the stable facade host systems call into.

Everything here is either a thin pass-through to the engine or a read-only
report. External callers never touch models, layers, or actors directly.
"""

from __future__ import annotations

from ple.core.paradox_pipeline import ParadoxLatticeEngine, PipelineResult
from ple.findings import finding_export
from ple.models.paradox import ParadoxState


def submit_frames(
    engine: ParadoxLatticeEngine, frames: list[dict], context: dict | None = None
) -> PipelineResult:
    """Submit two or more conflicting frames (model outputs, hypotheses,
    micro-mind positions) for paradox processing."""
    if len(frames) < 2:
        raise ValueError("paradox requires at least two frames")
    if len(frames) == 2:
        return engine.process(frames[0], frames[1], context)
    return engine.process_many(frames, context)


def get_findings(engine: ParadoxLatticeEngine, validated_only: bool = True) -> list[dict]:
    """Export all findings (read-only; the stored Findings are untouched
    apart from their export metadata)."""
    findings = engine.memory.findings
    if validated_only:
        findings = tuple(
            f for f in findings if f.validation_status == "validated"
        )
    return [finding_export.export(f, destination="external_api") for f in findings]


def ecology_report(engine: ParadoxLatticeEngine) -> dict:
    """Observability snapshot: the health of the paradox ecology."""
    active = engine.memory.get_active_paradoxes()
    attractors = engine.attractor_registry.all
    return {
        "active_paradoxes": len(active),
        "attenuated_paradoxes": sum(
            1 for p in active if p.state == ParadoxState.ATTENUATED
        ),
        "mean_intensity": (
            round(sum(p.intensity for p in active) / len(active), 6)
            if active
            else 0.0
        ),
        "lattice_nodes": len(engine.lattice.nodes),
        "lattice_edges": len(engine.lattice.edges),
        "global_tension": engine.lattice.global_tension,
        "attractors": {
            a.attractor_id: {
                "type": a.type,
                "state": a.state.value,
                "stability": a.stability_score,
            }
            for a in attractors
        },
        "episodes": len(engine.memory.episodes),
        "findings": len(engine.memory.findings),
        "recurring_lattice_patterns": len(
            engine.pattern_store.patterns(min_recurrence=2)
        ),
        "events_routed": len(engine.router.history),
    }
