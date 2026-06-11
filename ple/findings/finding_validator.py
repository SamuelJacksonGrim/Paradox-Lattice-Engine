"""Finding validation — only updates validation_status and confidence,
never the insight or lineage (finding_contract.md §4-5).
"""

from __future__ import annotations

from ple.attractors.attractor_registry import AttractorRegistry
from ple.models._mutation import authorized_set
from ple.models.attractor import AttractorState
from ple.models.finding import Finding

ACTOR = "finding_validator"


def validate(finding: Finding, registry: AttractorRegistry) -> str:
    """Check structural soundness; set validation_status accordingly."""
    attractor = registry.get_by_id(finding.attractor_id)
    checks = (
        attractor is not None,
        attractor is not None
        and attractor.state
        in (AttractorState.ACTIVE, AttractorState.STABILIZING),
        bool(finding.lineage),
        bool(finding.source_paradoxes),
        bool(finding.source_syntheses),
        attractor is not None
        and set(finding.source_syntheses) <= set(attractor.core_syntheses),
    )
    status = "validated" if all(checks) else "deprecated"
    authorized_set(finding, "validation_status", status, actor=ACTOR)
    if status == "validated" and attractor is not None:
        # Confidence tracks attractor stability (structural reliability, not truth).
        authorized_set(
            finding, "confidence", attractor.stability_score, actor=ACTOR
        )
    return status


def deprecate(finding: Finding) -> None:
    """Low-quality findings may be deprecated, never deleted."""
    authorized_set(finding, "validation_status", "deprecated", actor=ACTOR)
