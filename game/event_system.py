"""Priority-based procedural event system for turn-by-turn gameplay."""

from __future__ import annotations

from dataclasses import dataclass, field
from heapq import heappop, heappush


@dataclass(order=True)
class GameEvent:
    """Event item for priority queue processing."""

    priority: int
    turn: int
    name: str = field(compare=False)
    message: str = field(compare=False)


class EventQueue:
    """Min-heap event queue that returns highest priority events first."""

    def __init__(self) -> None:
        self._queue: list[GameEvent] = []

    def schedule(self, event: GameEvent) -> None:
        """Push a new event into the priority queue."""
        heappush(self._queue, event)

    def pop_ready(self, current_turn: int, max_events: int = 3) -> list[GameEvent]:
        """Pop events with turn <= current turn, constrained by max count."""
        ready: list[GameEvent] = []
        while self._queue and len(ready) < max_events:
            if self._queue[0].turn > current_turn:
                break
            ready.append(heappop(self._queue))
        return ready

    def size(self) -> int:
        """Return number of queued events."""
        return len(self._queue)
