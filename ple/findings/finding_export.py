"""Finding export — a read-only operation that preserves insight, lineage,
validation status, and confidence (finding_contract.md §8).
"""

from __future__ import annotations

import time

from ple.models._mutation import authorized_set
from ple.models.finding import Finding

ACTOR = "finding_export"


def export(finding: Finding, destination: str = "external") -> dict:
    payload = {
        "finding_id": finding.finding_id,
        "insight": finding.insight,
        "confidence": finding.confidence,
        "validation_status": finding.validation_status,
        "lineage": list(finding.lineage),
        "source_paradoxes": list(finding.source_paradoxes),
        "source_syntheses": list(finding.source_syntheses),
        "attractor_id": finding.attractor_id,
        "tension_profile": dict(finding.tension_profile),
    }
    meta = dict(finding.export_metadata)
    meta.setdefault("exports", [])
    meta["exports"] = list(meta["exports"]) + [
        {"destination": destination, "timestamp": time.time()}
    ]
    authorized_set(finding, "export_metadata", meta, actor=ACTOR)
    return payload
