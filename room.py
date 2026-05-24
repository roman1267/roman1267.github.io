"""Room domain model for the text-based adventure game."""

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class Room:
    """Represents a room in the game world."""

    name: str
    exits: Dict[str, str] = field(default_factory=dict)
    item: Optional[str] = None

    def can_move(self, direction: str) -> bool:
        """Return True if the room has an exit in the given direction."""
        return direction in self.exits

    def next_room(self, direction: str) -> Optional[str]:
        """Get the room name connected by the given direction."""
        return self.exits.get(direction)
