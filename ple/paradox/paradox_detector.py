"""Stage 1a — contradiction detection.

Frames are dicts of the conceptual shape:

    {"name": "frame_a", "claims": {"sky_color": "blue", ...},
     "evidence": ["..."], "context": {...}}

A raw contradiction is a shared claim key on which the two frames make
mutually exclusive assertions and which survives normalization
(non-triviality: rephrasing/canonicalization does not remove it).
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class RawContradiction:
    claim_key: str
    value_a: object
    value_b: object
    frame_a: str
    frame_b: str
    context: dict = field(default_factory=dict)


def _canonical(value: object) -> object:
    """Canonicalize a claim value so trivial rephrasings don't count as paradox."""
    if isinstance(value, str):
        return " ".join(value.strip().casefold().split())
    return value


def detect(frame_a: dict, frame_b: dict, context: dict | None = None) -> list[RawContradiction]:
    """Return contradictions between two frames within the same context window."""
    context = context or {}
    name_a = frame_a.get("name", "frame_a")
    name_b = frame_b.get("name", "frame_b")
    claims_a = frame_a.get("claims", {})
    claims_b = frame_b.get("claims", {})

    contradictions: list[RawContradiction] = []
    for key in sorted(set(claims_a) & set(claims_b)):
        va, vb = claims_a[key], claims_b[key]
        # Persistence under normalization: canonicalize before comparing.
        if _canonical(va) != _canonical(vb):
            contradictions.append(
                RawContradiction(
                    claim_key=key,
                    value_a=va,
                    value_b=vb,
                    frame_a=name_a,
                    frame_b=name_b,
                    context=dict(context),
                )
            )
    return contradictions
