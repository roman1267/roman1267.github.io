"""Combat and stat calculations for villain encounters."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .player import Player


@dataclass
class CombatResult:
    """Result payload from a resolved combat simulation."""

    outcome: str
    rounds: int
    player_hp: int
    enemy_hp: int
    summary: str


@dataclass
class EnemyProfile:
    """Enemy configuration loaded from the database or defaults."""

    name: str
    room: str
    base_hp: int
    base_attack: int
    base_defense: int
    item_attack_bonuses: dict[str, int]
    item_defense_bonuses: dict[str, int]


class CombatSystem:
    """Resolves villain encounters with stat and item modifiers."""

    def __init__(
        self,
        required_item_count: int = 6,
        enemy_profile: EnemyProfile | None = None,
        villain_room: str | None = None,
    ) -> None:
        self.required_item_count = required_item_count
        self.enemy_profile = enemy_profile or EnemyProfile(
            name="Phantom of Despair",
            room=villain_room or "Attic",
            base_hp=28,
            base_attack=9,
            base_defense=5,
            item_attack_bonuses={
                "Silver Knife": 4,
                "Crystal Orb": 3,
                "Cursed Amulet": 2,
                "Golden Ring": 1,
            },
            item_defense_bonuses={
                "Lantern of Shadows": 3,
                "Key": 1,
            },
        )
        if villain_room is not None:
            self.enemy_profile.room = villain_room

    def update_enemy_profile(self, enemy_profile: EnemyProfile) -> None:
        """Replace the active enemy profile from persisted database data."""
        self.enemy_profile = enemy_profile

    def resolve_encounter(self, player: Player) -> CombatResult:
        """Resolve encounter and return a detailed combat result."""
        if player.current_room != self.enemy_profile.room:
            return CombatResult(
                outcome="none",
                rounds=0,
                player_hp=0,
                enemy_hp=0,
                summary="No enemy encounter in this room.",
            )

        if player.inventory.size() < self.required_item_count:
            missing = self.required_item_count - player.inventory.size()
            return CombatResult(
                outcome="lose",
                rounds=0,
                player_hp=0,
                enemy_hp=self.enemy_profile.base_hp,
                summary=(
                    f"The {self.enemy_profile.name} overwhelms you before battle can begin. "
                    f"You still needed {missing} more item(s)."
                ),
            )

        return self._calculate_combat(player)

    def _calculate_combat(self, player: Player) -> CombatResult:
        """Simulate deterministic turn-based combat using derived stats."""
        inventory_items = player.inventory.to_list()

        player_hp = 24 + (player.inventory.size() * 3)
        player_attack = 8 + (player.inventory.size() * 2)
        player_defense = 4 + max(0, player.inventory.size() - 2)

        for item in inventory_items:
            player_attack += self.enemy_profile.item_attack_bonuses.get(item, 0)
            player_defense += self.enemy_profile.item_defense_bonuses.get(item, 0)

        enemy_hp = self.enemy_profile.base_hp + max(0, 2 - (player.inventory.size() // 3))
        enemy_attack = self.enemy_profile.base_attack
        enemy_defense = self.enemy_profile.base_defense

        rounds = 0
        variance_cycle = [0, 1, -1, 2, -2]
        checksum = sum(ord(character) for item in inventory_items for character in item)

        while player_hp > 0 and enemy_hp > 0 and rounds < 20:
            variance = variance_cycle[(rounds + checksum) % len(variance_cycle)]

            player_damage = max(1, player_attack + variance - (enemy_defense // 2))
            enemy_hp -= player_damage
            if enemy_hp <= 0:
                rounds += 1
                break

            enemy_damage = max(1, enemy_attack - variance - (player_defense // 2))
            player_hp -= enemy_damage
            rounds += 1

        if enemy_hp <= 0 and player_hp > 0:
            return CombatResult(
                outcome="win",
                rounds=rounds,
                player_hp=max(player_hp, 0),
                enemy_hp=max(enemy_hp, 0),
                summary=f"Victory in {rounds} rounds! You reduced the {self.enemy_profile.name} to 0 HP.",
            )

        return CombatResult(
            outcome="lose",
            rounds=rounds,
            player_hp=max(player_hp, 0),
            enemy_hp=max(enemy_hp, 0),
            summary=f"Defeat. The {self.enemy_profile.name} outlasted your strength.",
        )
