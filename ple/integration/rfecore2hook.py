"""RFE-Core2 hook — per-cycle evaluator signals -> paradox frames.

RFE-Core2's autonomous cycle runs several evaluators side by side every step
(the watcher's three coherence components, the field-delta trend, the
emotional gradient, the rhythm router, governance, and the manipulation
resistance engine). Each holds an opinion about the same underlying
situation; when those opinions diverge, that disagreement is exactly the
contradiction substrate PLE feeds on.

This hook is the bridge its host calls once per cycle: it discretizes the
raw telemetry into eight evaluator frames (frame defs v1) and submits them
through the external API. PLE stays dormant on cycles where every evaluator
agrees — dormancy is correct behavior, not a bug.

The hook is read-only with respect to the engine: it builds plain frame
dicts and calls ``submit_frames``; it never touches models, layers, or
actor-guarded fields. It imports nothing from RFE-Core2 — the host supplies
a plain telemetry dict.

Frame defs v1 — shared claim keys are what make contradictions detectable
and recurrence (same frame pair, same claim key) what forms attractors:

    frame               claim keys                  values
    -----------------   -------------------------   -------------------------
    watcher_geometric   coherence_band              low | mid | high
    watcher_temporal    coherence_band              low | mid | high
    watcher_resonance   coherence_band              low | mid | high
    field_delta         trajectory_sign             improving | flat | degrading
    emotion             trajectory_sign, posture    (valence sign; dominant emotion)
    rhythm_router       posture                     explore | consolidate
    governance          threat_level                none | elevated | high
    resistance          threat_level                none | elevated | high
"""

from __future__ import annotations

from ple.core.paradox_pipeline import ParadoxLatticeEngine, PipelineResult
from ple.integration.external_api import submit_frames

# Convention only — the hook performs no guarded mutations.
ACTOR = "rfecore2hook"

# Discretization v1. The coherence bands echo RFE's crystallization
# coherence threshold (0.75); the severity bands mirror RFE's compound
# manipulation-severity response bands (0.30 / 0.60).
COHERENCE_LOW = 0.45
COHERENCE_HIGH = 0.75
DELTA_DEADBAND = 0.01
VALENCE_DEADBAND = 0.05
SEVERITY_ELEVATED = 0.30
SEVERITY_HIGH = 0.60

EXPLORATORY_EMOTIONS = frozenset({"curiosity", "wonder", "boredom"})
CONSOLIDATING_EMOTIONS = frozenset({"stability", "joy", "tension"})
EXPLORATORY_RHYTHMS = frozenset({"reflect", "explore"})
CONSOLIDATING_RHYTHMS = frozenset({"stabilize", "dream"})
BENIGN_DECISIONS = frozenset({"allow"})
ELEVATED_DECISIONS = frozenset({"monitor", "allow_weakened"})
HIGH_DECISIONS = frozenset({"quarantine", "reject", "sacred_shield"})

REQUIRED_KEYS = (
    "watcher_geometric",
    "watcher_temporal",
    "watcher_resonance",
    "coherence_delta",
    "valence",
    "dominant_emotion",
    "decision",
    "manipulation_severity",
    "rhythm",
)


def _coherence_band(value: float) -> str:
    if value < COHERENCE_LOW:
        return "low"
    if value < COHERENCE_HIGH:
        return "mid"
    return "high"


def _trajectory_sign(value: float, deadband: float) -> str:
    if value > deadband:
        return "improving"
    if value < -deadband:
        return "degrading"
    return "flat"


def _emotion_posture(dominant_emotion: str) -> str:
    return "explore" if dominant_emotion in EXPLORATORY_EMOTIONS else "consolidate"


def _rhythm_posture(rhythm: str) -> str:
    return "explore" if rhythm in EXPLORATORY_RHYTHMS else "consolidate"


def _governance_threat(decision: str) -> str:
    decision = decision.strip().casefold()
    if decision in BENIGN_DECISIONS:
        return "none"
    if decision in ELEVATED_DECISIONS:
        return "elevated"
    return "high"


def _severity_threat(severity: float) -> str:
    if severity < SEVERITY_ELEVATED:
        return "none"
    if severity < SEVERITY_HIGH:
        return "elevated"
    return "high"


def frames_from_cycle(telemetry: dict) -> list[dict]:
    """Discretize one cycle's evaluator telemetry into eight frames.

    ``telemetry`` must carry every key in ``REQUIRED_KEYS``:

        watcher_geometric / watcher_temporal / watcher_resonance : float
        coherence_delta : float        (signed field change)
        valence : float                (affective trajectory, [-1, 1])
        dominant_emotion : str         (one of the six emotional scalars)
        decision : str                 (GovernanceDecision name)
        manipulation_severity : float  (sum of active signal severities)
        rhythm : str                   (routed rhythm band)
    """
    missing = [k for k in REQUIRED_KEYS if k not in telemetry]
    if missing:
        raise ValueError(f"telemetry missing required keys: {missing}")

    return [
        {
            "name": "watcher_geometric",
            "claims": {"coherence_band": _coherence_band(telemetry["watcher_geometric"])},
        },
        {
            "name": "watcher_temporal",
            "claims": {"coherence_band": _coherence_band(telemetry["watcher_temporal"])},
        },
        {
            "name": "watcher_resonance",
            "claims": {"coherence_band": _coherence_band(telemetry["watcher_resonance"])},
        },
        {
            "name": "field_delta",
            "claims": {
                "trajectory_sign": _trajectory_sign(
                    telemetry["coherence_delta"], DELTA_DEADBAND
                )
            },
        },
        {
            "name": "emotion",
            "claims": {
                "trajectory_sign": _trajectory_sign(
                    telemetry["valence"], VALENCE_DEADBAND
                ),
                "posture": _emotion_posture(telemetry["dominant_emotion"]),
            },
        },
        {
            "name": "rhythm_router",
            "claims": {"posture": _rhythm_posture(telemetry["rhythm"])},
        },
        {
            "name": "governance",
            "claims": {"threat_level": _governance_threat(telemetry["decision"])},
        },
        {
            "name": "resistance",
            "claims": {
                "threat_level": _severity_threat(telemetry["manipulation_severity"])
            },
        },
    ]


def submit_cycle(
    engine: ParadoxLatticeEngine,
    telemetry: dict,
    context: dict | None = None,
) -> PipelineResult:
    """Submit one RFE-Core2 cycle's evaluator frames for paradox processing.

    Returns the ``PipelineResult``; ``result.triggered`` is False on cycles
    where every evaluator agrees (the common case — PLE stays dormant).
    """
    return submit_frames(engine, frames_from_cycle(telemetry), context)
