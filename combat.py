"""Simple combat/encounter resolution."""

from player import Player


class CombatSystem:
    """Resolves villain encounters."""

    def __init__(self, villain_room: str, required_item_count: int) -> None:
        self.villain_room = villain_room
        self.required_item_count = required_item_count

    def resolve_encounter(self, player: Player) -> str:
        """Return encounter state: 'win', 'lose', or 'none'."""
        if player.current_room != self.villain_room:
            return "none"

        if player.inventory.size() >= self.required_item_count:
            return "win"

        return "lose"
