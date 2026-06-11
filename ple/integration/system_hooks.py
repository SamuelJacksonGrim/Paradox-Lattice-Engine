"""System hooks — how host architectures (LAE, Chimera Core, RFE-Core2)
listen to PLE without touching its internals.

Hooks are read-only observers over the typed event stream. A bridge
registers callbacks for the event classes it cares about; PLE never blocks
on a hook, and a hook can never mutate engine state through the
subscription (it receives frozen event objects).
"""

from __future__ import annotations

from typing import Callable

from ple import events
from ple.core.paradox_pipeline import ParadoxLatticeEngine

HOOKABLE_EVENTS = {
    "paradox": events.ParadoxEvent,
    "tension_field": events.TensionFieldEvent,
    "lattice": events.LatticeUpdateEvent,
    "synthesis": events.SynthesisEvent,
    "resolution": events.ResolutionEvent,
    "attractor": events.AttractorEvent,
    "finding": events.FindingEvent,
    "memory": events.MemoryEvent,
}


def register(
    engine: ParadoxLatticeEngine, channel: str, callback: Callable
) -> None:
    """Subscribe a host-system callback to a PLE event channel.

    Channels: paradox | tension_field | lattice | synthesis | resolution |
    attractor | finding | memory
    """
    event_class = HOOKABLE_EVENTS.get(channel)
    if event_class is None:
        raise ValueError(
            f"unknown hook channel {channel!r}; "
            f"available: {sorted(HOOKABLE_EVENTS)}"
        )
    engine.router.subscribe(event_class, callback)


def register_transition_trigger(
    engine: ParadoxLatticeEngine, callback: Callable
) -> None:
    """LAE-style integration: paradox-driven tension treated as a transition
    trigger. Fires the callback whenever a tension field is generated or an
    attractor's resolution horizon is crossed."""
    engine.router.subscribe(events.TensionFieldEvent, callback)
    engine.router.subscribe(events.ResolutionEvent, callback)
