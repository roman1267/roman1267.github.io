"""Room domain model for the text-based adventure game."""

from dataclasses import dataclass, field
from typing import Optional


def _empty_exits() -> dict[str, str]:
    """Create a typed empty exits mapping for dataclass defaults."""
    return {}


@dataclass
class Room:
    """Represents a room in the game world."""

    name: str
    exits: dict[str, str] = field(default_factory=_empty_exits)
    item: Optional[str] = None

    def can_move(self, direction: str) -> bool:
        """Return True if the room has an exit in the given direction."""
        return direction in self.exits

    def next_room(self, direction: str) -> Optional[str]:
        """Get the room name connected by the given direction."""
        return self.exits.get(direction)
