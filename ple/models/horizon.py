"""ResolutionHorizon model — a boundary where paradox might collapse but hasn't yet."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from ple.errors import ContractViolation


@dataclass(frozen=True)
class ResolutionHorizon:
    paradox_ids: tuple[str, ...]
    collapse_probability: float
    stability_window: dict = field(default_factory=lambda: {"start": 0.0, "end": 1.0})
    triggers: tuple[str, ...] = ()
    horizon_id: str = field(default_factory=lambda: f"rh-{uuid.uuid4().hex[:12]}")

    def __post_init__(self) -> None:
        if not self.paradox_ids:
            raise ContractViolation("a resolution horizon requires paradoxes")
        if not (0.0 <= self.collapse_probability <= 1.0):
            raise ContractViolation("collapse_probability must be within [0.0, 1.0]")
