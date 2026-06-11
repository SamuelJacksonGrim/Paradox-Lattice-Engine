"""Finding model — see finding_contract.md."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from ple.errors import ContractViolation

VALIDATION_STATUSES = frozenset({"unvalidated", "validated", "deprecated"})


@dataclass(frozen=True)
class Finding:
    """The final cognitive output of PLE: a distilled, validated,
    structurally-grounded insight emerging from attractor dynamics.

    Immutable except for validation_status / confidence (finding_validator
    only) and export_metadata (finding_export only).
    """

    attractor_id: str
    source_syntheses: tuple[str, ...]
    source_paradoxes: tuple[str, ...]
    insight: str
    confidence: float
    tension_profile: dict = field(default_factory=dict)
    lineage: tuple[str, ...] = ()
    validation_status: str = "unvalidated"
    export_metadata: dict = field(default_factory=dict)
    finding_id: str = field(default_factory=lambda: f"fd-{uuid.uuid4().hex[:12]}")

    def __post_init__(self) -> None:
        if not self.source_syntheses:
            raise ContractViolation("source_syntheses must be non-empty")
        if not self.source_paradoxes:
            raise ContractViolation("source_paradoxes must be non-empty")
        if not self.insight.strip():
            raise ContractViolation("insight must be a coherent statement")
        if not (0.0 <= self.confidence <= 1.0):
            raise ContractViolation("confidence must be within [0.0, 1.0]")
        if self.validation_status not in VALIDATION_STATUSES:
            raise ContractViolation(
                f"invalid validation_status {self.validation_status!r}"
            )
