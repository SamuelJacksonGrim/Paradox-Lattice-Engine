"""Stage 1b — contradiction type classification.

Types (TYPES.md): logical | semantic | contextual | self_referential
"""

from __future__ import annotations

from ple.paradox.paradox_detector import RawContradiction


def classify(contradiction: RawContradiction, context: dict | None = None) -> str:
    context = context or contradiction.context

    # Self-referential: a frame's claim refers back to itself or its sibling.
    referents = {contradiction.frame_a, contradiction.frame_b, "self"}
    for value in (contradiction.value_a, contradiction.value_b):
        if isinstance(value, str) and any(ref in value for ref in referents):
            return "self_referential"

    # Contextual: the frames are scoped to different declared domains.
    domains = context.get("frame_domains", {})
    da = domains.get(contradiction.frame_a)
    db = domains.get(contradiction.frame_b)
    if da is not None and db is not None and da != db:
        return "contextual"

    # Logical: directly opposed boolean claims.
    if isinstance(contradiction.value_a, bool) and isinstance(
        contradiction.value_b, bool
    ):
        return "logical"

    return "semantic"
