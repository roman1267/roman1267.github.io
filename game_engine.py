"""Main game engine that orchestrates gameplay systems."""

from __future__ import annotations

import time
from typing import Dict, Optional

from combat import CombatSystem
from database import DatabaseError, MongoGameRepository
from inventory import Inventory
from player import Player
from room import Room


class GameEngine:
    """Coordinates room state, player actions, persistence, and game flow."""

    def __init__(self, sleep_seconds: float = 0.4) -> None:
        self.sleep_seconds = sleep_seconds
        self.rooms = self._build_rooms()
        self.player = Player(current_room="Garden", inventory=Inventory())
        self.required_items = 6
        self.combat = CombatSystem(villain_room="Attic", required_item_count=self.required_items)
        self.repository = MongoGameRepository()
        self.is_running = True

    @staticmethod
    def _build_rooms() -> Dict[str, Room]:
        """Create configurable room graph and room items."""
        return {
            "Entrance Hall": Room(
                name="Entrance Hall",
                exits={
                    "North": "Dining Room",
                    "East": "Master Bedroom",
                    "South": "Library",
                    "West": "Garden",
                },
                item="Crystal Orb",
            ),
            "Library": Room(name="Library", exits={"North": "Entrance Hall", "East": "Basement"}, item="Key"),
            "Dining Room": Room(
                name="Dining Room",
                exits={"South": "Entrance Hall", "East": "Kitchen"},
                item="Cursed Amulet",
            ),
            "Kitchen": Room(name="Kitchen", exits={"West": "Dining Room"}, item="Silver Knife"),
            "Basement": Room(name="Basement", exits={"West": "Library"}, item="Lantern of Shadows"),
            "Master Bedroom": Room(
                name="Master Bedroom",
                exits={"West": "Entrance Hall", "North": "Attic"},
                item="Golden Ring",
            ),
            "Attic": Room(name="Attic", exits={}, item=None),
            "Garden": Room(name="Garden", exits={"East": "Entrance Hall"}, item=None),
        }

    def initialize(self) -> str:
        """Initialize systems and return startup message."""
        try:
            self.repository.connect()
            db_state = "MongoDB connected"
        except DatabaseError as exc:
            db_state = f"MongoDB unavailable ({exc}). Save/load commands will be disabled."

        return (
            "Welcome to Haunted Mansion Escape! Collect all items to defeat the Phantom of Despair.\n"
            f"System status: {db_state}"
        )

    def format_status(self) -> str:
        """Render current room, inventory, exits, and room item."""
        room = self.rooms[self.player.current_room]
        inventory_display = ", ".join(self.player.inventory.to_list()) or "Empty"
        exits_display = ", ".join(room.exits.keys()) or "None"

        lines = [
            "\n" + "=" * 64,
            f"Location : {room.name}",
            f"Inventory: {inventory_display}",
            f"Exits    : {exits_display}",
            "-" * 64,
        ]

        if room.item:
            lines.append(f"You see a {room.item} here.")
        else:
            lines.append("There are no items in this room.")

        lines.append("=" * 64)
        return "\n".join(lines)

    def process_command(self, raw_command: str) -> str:
        """Parse and execute a user command."""
        tokens = raw_command.strip().split()
        if not tokens:
            return "Please enter a command."

        command = tokens[0].lower()

        if command == "go":
            if len(tokens) < 2:
                return "Go where? Use: go <North|South|East|West>."
            return self._handle_move(tokens[1].capitalize())

        if command == "get":
            if len(tokens) < 2:
                return "Get what? Use: get <item name>."
            return self._handle_get_item(" ".join(tokens[1:]))

        if command == "inventory":
            display = ", ".join(self.player.inventory.to_list()) or "Empty"
            return f"Inventory: {display}"

        if command == "save":
            slot = tokens[1] if len(tokens) > 1 else "default"
            return self._handle_save(slot)

        if command == "load":
            slot = tokens[1] if len(tokens) > 1 else "default"
            return self._handle_load(slot)

        if command == "saves":
            return self._handle_list_saves()

        if command == "help":
            return (
                "Commands: go <direction>, get <item>, inventory, save [slot], "
                "load [slot], saves, help, quit"
            )

        if command == "quit":
            self.is_running = False
            return "Exiting game."

        return "Invalid command. Type 'help' to see available commands."

    def _handle_move(self, direction: str) -> str:
        room = self.rooms[self.player.current_room]
        if not room.can_move(direction):
            return "You cannot go that way."

        next_room_name = room.next_room(direction)
        if next_room_name is None:
            return "You cannot go that way."

        self.player.move_to(next_room_name)
        outcome = self.combat.resolve_encounter(self.player)
        if outcome == "win":
            self.is_running = False
            return "Congratulations! You defeated the Phantom of Despair and escaped!"
        if outcome == "lose":
            self.is_running = False
            return "The Phantom of Despair consumed your courage... GAME OVER."

        return f"You move {direction} into the {next_room_name}."

    def _handle_get_item(self, item_name: str) -> str:
        room = self.rooms[self.player.current_room]
        if room.item is None:
            return "There is nothing to pick up here."

        if room.item != item_name:
            return "That item is not in this room."

        self.player.inventory.add(item_name)
        room.item = None
        return f"{item_name} retrieved."

    def _handle_save(self, slot: str) -> str:
        try:
            self.repository.save_game(slot, self.player)
            return f"Game saved to slot '{slot}'."
        except DatabaseError as exc:
            return f"Save failed: {exc}"
        except Exception as exc:
            return f"Save failed: {exc}"

    def _handle_load(self, slot: str) -> str:
        try:
            data = self.repository.load_game(slot)
        except DatabaseError as exc:
            return f"Load failed: {exc}"
        except Exception as exc:
            return f"Load failed: {exc}"

        if not data:
            return f"No save found for slot '{slot}'."

        player_data = data.get("player", {})
        saved_room = player_data.get("current_room")
        if saved_room not in self.rooms:
            return "Load failed: save data is invalid."

        self.player.current_room = saved_room
        self.player.inventory = Inventory.from_iterable(player_data.get("inventory", []))
        return f"Game loaded from slot '{slot}'."

    def _handle_list_saves(self) -> str:
        try:
            saves = self.repository.list_saves()
        except DatabaseError as exc:
            return f"Unable to list saves: {exc}"
        except Exception as exc:
            return f"Unable to list saves: {exc}"

        if not saves:
            return "No saves found."

        lines = ["Save slots:"]
        for save in saves:
            lines.append(f"- {save.get('slot', 'unknown')} ({save.get('updated_at', 'n/a')})")
        return "\n".join(lines)

    def shutdown(self) -> None:
        """Cleanly close external resources."""
        self.repository.close()

    def loop_delay(self) -> None:
        """Small pause to preserve the original game's pacing."""
        time.sleep(self.sleep_seconds)
