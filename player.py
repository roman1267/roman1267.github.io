"""Player domain model."""

from dataclasses import dataclass

from inventory import Inventory


@dataclass
class Player:
    """Represents the user-controlled character."""

    current_room: str
    inventory: Inventory

    def move_to(self, room_name: str) -> None:
        """Update player's current location."""
        self.current_room = room_name
