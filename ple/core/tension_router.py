"""Tension Router — routes typed events to subscribed layers.

Supports feedback (synthesis influencing lattice, lattice influencing tension
fields) and re-entrant processing when paradoxes intensify or reappear.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Callable


class TensionRouter:
    def __init__(self) -> None:
        self._subscribers: dict[type, list[Callable]] = defaultdict(list)
        self._history: list = []

    def subscribe(self, event_class: type, handler: Callable) -> None:
        self._subscribers[event_class].append(handler)

    def emit(self, event) -> None:
        self._history.append(event)
        for handler in self._subscribers[type(event)]:
            handler(event)

    @property
    def history(self) -> tuple:
        return tuple(self._history)

    def events_of(self, event_class: type) -> tuple:
        return tuple(e for e in self._history if isinstance(e, event_class))
