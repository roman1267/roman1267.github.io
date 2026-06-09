from game.combat import CombatSystem
from game.inventory import Inventory
from game.player import Player


ALL_ITEMS = [
    "Crystal Orb",
    "Key",
    "Cursed Amulet",
    "Silver Knife",
    "Lantern of Shadows",
    "Golden Ring",
]


def test_combat_wins_with_all_required_items() -> None:
    inventory = Inventory.from_iterable(ALL_ITEMS)
    player = Player(current_room="Attic", inventory=inventory)
    combat = CombatSystem(villain_room="Attic", required_item_count=6)

    result = combat.resolve_encounter(player)

    assert result.outcome == "win"
    assert result.rounds > 0
    assert result.enemy_hp == 0


def test_combat_loses_when_missing_required_items() -> None:
    inventory = Inventory.from_iterable(["Crystal Orb", "Key"])
    player = Player(current_room="Attic", inventory=inventory)
    combat = CombatSystem(villain_room="Attic", required_item_count=6)

    result = combat.resolve_encounter(player)

    assert result.outcome == "lose"
    assert result.rounds == 0
    assert "needed 4 more item" in result.summary
