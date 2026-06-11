"""Registry of attractors keyed by recurrence signature.

Attractors must never be deleted or overwritten — the registry is append-only
per signature.
"""

from __future__ import annotations

from ple.errors import ContractViolation
from ple.models.attractor import Attractor


class AttractorRegistry:
    def __init__(self) -> None:
        self._by_signature: dict[tuple, Attractor] = {}
        self._by_id: dict[str, Attractor] = {}

    def get(self, signature: tuple) -> Attractor | None:
        return self._by_signature.get(signature)

    def get_by_id(self, attractor_id: str) -> Attractor | None:
        return self._by_id.get(attractor_id)

    def register(self, signature: tuple, attractor: Attractor) -> Attractor:
        if signature in self._by_signature:
            raise ContractViolation(
                "attractors must not be overwritten by new attractors"
            )
        self._by_signature[signature] = attractor
        self._by_id[attractor.attractor_id] = attractor
        return attractor

    @property
    def all(self) -> tuple[Attractor, ...]:
        return tuple(self._by_id.values())
