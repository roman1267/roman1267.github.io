"""Main game engine that orchestrates gameplay systems."""

from __future__ import annotations

import time
from typing import Callable, Dict

from combat import CombatResult, CombatSystem, EnemyProfile
from database import DatabaseError, MongoGameRepository
from event_system import EventQueue, GameEvent
from inventory import Inventory
from player import Player
from room import Room
from world_graph import WorldGraph


def _normalize_text(value: str) -> str:
    """Normalize user text for dictionary-based lookups."""
    return " ".join(value.strip().lower().split())


class GameEngine:
    """Coordinates room state, player actions, persistence, and game flow."""

    def __init__(self, sleep_seconds: float = 0.4) -> None:
        self.sleep_seconds = sleep_seconds
        self.rooms = self._build_rooms()
        self.world = self._build_world_graph(self.rooms)
        self.room_lookup = { _normalize_text(name): name for name in self.rooms }
        self.item_lookup = self._build_item_lookup(self.rooms)
        self.player = Player(current_room="Garden", inventory=Inventory())
        self.required_items = 6
        self.enemy_profile = self._build_default_enemy_profile()
        self.combat = CombatSystem(required_item_count=self.required_items, enemy_profile=self.enemy_profile)
        self.repository = MongoGameRepository()
        self.event_queue = EventQueue()
        self.turn_counter = 0
        self.command_aliases = {
            "move": "go",
            "walk": "go",
            "take": "get",
            "pick": "get",
            "inv": "inventory",
            "i": "inventory",
            "path": "route",
            "exit": "quit",
            "l": "look",
        }
        self.direction_aliases = {
            "n": "North",
            "s": "South",
            "e": "East",
            "w": "West",
            "north": "North",
            "south": "South",
            "east": "East",
            "west": "West",
        }
        self.command_handlers: dict[str, Callable[[list[str]], str]] = {
            "go": self._cmd_go,
            "get": self._cmd_get,
            "inventory": self._cmd_inventory,
            "save": self._cmd_save,
            "load": self._cmd_load,
            "saves": self._cmd_saves,
            "help": self._cmd_help,
            "route": self._cmd_route,
            "look": self._cmd_look,
            "quit": self._cmd_quit,
        }
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

    @staticmethod
    def _build_world_graph(rooms: Dict[str, Room]) -> WorldGraph:
        """Build graph from room exit mappings for traversal algorithms."""
        world = WorldGraph()
        for room_name, room in rooms.items():
            world.add_room(room_name)
            for direction, destination in room.exits.items():
                world.add_edge(room_name, direction, destination)
        return world

    @staticmethod
    def _build_item_lookup(rooms: Dict[str, Room]) -> dict[str, str]:
        """Create normalized item lookup map for scalable name resolution."""
        item_lookup: dict[str, str] = {}
        for room in rooms.values():
            if room.item:
                item_lookup[_normalize_text(room.item)] = room.item
        return item_lookup

    @staticmethod
    def _build_default_enemy_profile() -> EnemyProfile:
        """Create the default enemy profile used when MongoDB has no enemy seed."""
        return EnemyProfile(
            name="Phantom of Despair",
            room="Attic",
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

    def initialize(self) -> str:
        """Initialize systems and return startup message."""
        try:
            self.repository.connect()
            self.rooms = self.repository.load_or_seed_rooms(self.rooms)
            enemy_doc = self.repository.load_or_seed_enemy(
                {
                    "name": self.enemy_profile.name,
                    "room": self.enemy_profile.room,
                    "base_hp": self.enemy_profile.base_hp,
                    "base_attack": self.enemy_profile.base_attack,
                    "base_defense": self.enemy_profile.base_defense,
                    "item_attack_bonuses": self.enemy_profile.item_attack_bonuses,
                    "item_defense_bonuses": self.enemy_profile.item_defense_bonuses,
                }
            )
            self.enemy_profile = self._enemy_profile_from_doc(enemy_doc)
            self.combat.update_enemy_profile(self.enemy_profile)
            self.world = self._build_world_graph(self.rooms)
            self.room_lookup = {_normalize_text(name): name for name in self.rooms}
            self.item_lookup = self._build_item_lookup(self.rooms)
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
        inventory_display = ", ".join(self.player.inventory.to_detailed_list()) or "Empty"
        exits_display = ", ".join(self.world.directions_from(room.name).keys()) or "None"

        lines = [
            "\n" + "=" * 64,
            f"Location : {room.name}",
            f"Inventory: {inventory_display}",
            f"Exits    : {exits_display}",
            f"Turn     : {self.turn_counter}",
            "-" * 64,
        ]

        if room.item:
            lines.append(f"You see a {room.item} here.")
        else:
            lines.append("There are no items in this room.")

        lines.append("=" * 64)
        return "\n".join(lines)

    def process_command(self, raw_command: str) -> str:
        """Parse and execute a user command using dispatch table lookup."""
        command, args = self._parse_command(raw_command)
        if not command:
            return "Please enter a command."

        handler = self.command_handlers.get(command)
        if handler is None:
            return "Invalid command. Type 'help' to see available commands."

        return handler(args)

    def _parse_command(self, raw_command: str) -> tuple[str, list[str]]:
        """Tokenize and normalize command names for constant-time dispatch."""
        tokens = raw_command.strip().split()
        if not tokens:
            return "", []

        command = tokens[0].lower()
        command = self.command_aliases.get(command, command)
        return command, tokens[1:]

    def _cmd_go(self, args: list[str]) -> str:
        if not args:
            return "Go where? Use: go <North|South|East|West>."

        direction_key = args[0].lower()
        direction = self.direction_aliases.get(direction_key)
        if direction is None:
            return "Unknown direction. Use North, South, East, or West."

        if not self.world.can_move(self.player.current_room, direction):
            return "You cannot go that way."

        next_room_name = self.world.next_room(self.player.current_room, direction)
        if next_room_name is None:
            return "You cannot go that way."

        self.player.move_to(next_room_name)
        self.turn_counter += 1
        self._schedule_procedural_events(next_room_name)
        try:
            self.repository.log_session_event(
                slot="runtime",
                event_name="move",
                details={"direction": direction, "room": next_room_name, "turn_counter": self.turn_counter},
            )
        except DatabaseError:
            pass

        combat_result = self.combat.resolve_encounter(self.player)
        if combat_result.outcome == "win":
            try:
                self.repository.log_session_event(
                    slot="runtime",
                    event_name="combat_win",
                    details={"room": next_room_name, "turn_counter": self.turn_counter},
                )
            except DatabaseError:
                pass
            self.is_running = False
            return (
                "Congratulations! You defeated the Phantom of Despair and escaped!\n"
                f"{combat_result.summary}"
            )
        if combat_result.outcome == "lose":
            try:
                self.repository.log_session_event(
                    slot="runtime",
                    event_name="combat_lose",
                    details={"room": next_room_name, "turn_counter": self.turn_counter},
                )
            except DatabaseError:
                pass
            self.is_running = False
            return f"The Phantom of Despair consumed your courage... GAME OVER.\n{combat_result.summary}"

        event_messages = self._process_ready_events()
        if event_messages:
            return f"You move {direction} into the {next_room_name}.\n" + "\n".join(event_messages)

        return f"You move {direction} into the {next_room_name}."

    def _cmd_get(self, args: list[str]) -> str:
        if not args:
            return "Get what? Use: get <item name>."
        return self._handle_get_item(" ".join(args))

    def _cmd_inventory(self, _args: list[str]) -> str:
        display = ", ".join(self.player.inventory.to_detailed_list()) or "Empty"
        return f"Inventory: {display}"

    def _cmd_save(self, args: list[str]) -> str:
        slot = args[0] if args else "default"
        return self._handle_save(slot)

    def _cmd_load(self, args: list[str]) -> str:
        slot = args[0] if args else "default"
        return self._handle_load(slot)

    def _cmd_saves(self, _args: list[str]) -> str:
        return self._handle_list_saves()

    def _cmd_help(self, _args: list[str]) -> str:
        return (
            "Commands: go <direction>, get <item>, inventory, route <room>, look, "
            "save [slot], load [slot], saves, help, quit"
        )

    def _cmd_route(self, args: list[str]) -> str:
        if not args:
            return "Route where? Use: route <room name>."

        target_input = " ".join(args)
        target_room = self.room_lookup.get(_normalize_text(target_input))
        if target_room is None:
            return "Unknown room name."

        if target_room == self.player.current_room:
            return "You are already in that room."

        path_rooms = self.world.shortest_path_rooms(self.player.current_room, target_room)
        path_directions = self.world.shortest_path_directions(self.player.current_room, target_room)

        if not path_rooms or not path_directions:
            return "No route is currently available."

        room_string = " -> ".join(path_rooms)
        direction_string = " -> ".join(path_directions)
        return (
            f"Shortest route to {target_room}: {direction_string}\n"
            f"Room path: {room_string}"
        )

    def _cmd_look(self, _args: list[str]) -> str:
        room = self.rooms[self.player.current_room]
        exits_display = ", ".join(self.world.directions_from(room.name).keys()) or "None"
        if room.item:
            return f"You are in {room.name}. Exits: {exits_display}. You see {room.item}."
        return f"You are in {room.name}. Exits: {exits_display}."

    def _cmd_quit(self, _args: list[str]) -> str:
        self.is_running = False
        return "Exiting game."

    def _schedule_procedural_events(self, entered_room: str) -> None:
        """Create deterministic procedural events using turn counters and context."""
        if self.turn_counter % 2 == 0:
            self.event_queue.schedule(
                GameEvent(
                    priority=2,
                    turn=self.turn_counter,
                    name="whispers",
                    message="A whisper crawls along the walls: 'Turn back while you can...'",
                )
            )

        if entered_room == "Basement" and not self.player.inventory.contains("Lantern of Shadows"):
            self.event_queue.schedule(
                GameEvent(
                    priority=1,
                    turn=self.turn_counter,
                    name="darkness",
                    message="The darkness thickens. A lantern here might be useful.",
                )
            )

        if self.turn_counter % 3 == 0:
            self.event_queue.schedule(
                GameEvent(
                    priority=3,
                    turn=self.turn_counter + 1,
                    name="temperature_drop",
                    message="The temperature suddenly drops as a shadow moves nearby.",
                )
            )

    def _process_ready_events(self) -> list[str]:
        """Process due events by priority and return user-facing messages."""
        ready = self.event_queue.pop_ready(current_turn=self.turn_counter)
        if not ready:
            return []
        return [f"[Event] {event.message}" for event in ready]

    @staticmethod
    def _enemy_profile_from_doc(enemy_doc: Dict[str, object]) -> EnemyProfile:
        """Normalize a persisted enemy document into a typed profile object."""
        def _as_int(value: object, default: int) -> int:
            return value if isinstance(value, int) else default

        def _as_bonus_map(value: object, default: dict[str, int]) -> dict[str, int]:
            if not isinstance(value, dict):
                return default
            result: dict[str, int] = {}
            for key, raw_value in value.items():
                if isinstance(key, str) and isinstance(raw_value, int):
                    result[key] = raw_value
            return result or default

        return EnemyProfile(
            name=str(enemy_doc.get("name", "Phantom of Despair")),
            room=str(enemy_doc.get("room", "Attic")),
            base_hp=_as_int(enemy_doc.get("base_hp"), 28),
            base_attack=_as_int(enemy_doc.get("base_attack"), 9),
            base_defense=_as_int(enemy_doc.get("base_defense"), 5),
            item_attack_bonuses=_as_bonus_map(
                enemy_doc.get("item_attack_bonuses"),
                {
                    "Silver Knife": 4,
                    "Crystal Orb": 3,
                    "Cursed Amulet": 2,
                    "Golden Ring": 1,
                },
            ),
            item_defense_bonuses=_as_bonus_map(
                enemy_doc.get("item_defense_bonuses"),
                {
                    "Lantern of Shadows": 3,
                    "Key": 1,
                },
            ),
        )

    def _handle_get_item(self, item_name: str) -> str:
        room = self.rooms[self.player.current_room]
        if room.item is None:
            return "There is nothing to pick up here."

        requested_item = self.item_lookup.get(_normalize_text(item_name), item_name)
        if room.item != requested_item:
            return "That item is not in this room."

        self.player.inventory.add(room.item)
        self.item_lookup.pop(_normalize_text(room.item), None)
        room.item = None
        try:
            self.repository.log_session_event(
                slot="runtime",
                event_name="pickup",
                details={"item": requested_item, "room": self.player.current_room, "turn_counter": self.turn_counter},
            )
        except DatabaseError:
            pass
        return f"{requested_item} retrieved."

    def _handle_save(self, slot: str) -> str:
        try:
            self.repository.save_game(slot, self.player, turn_counter=self.turn_counter)
            self.repository.log_session_event(
                slot=slot,
                event_name="save_command",
                details={"current_room": self.player.current_room, "turn_counter": self.turn_counter},
            )
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
        raw_turn_counter = data.get("turn_counter", 0)
        if isinstance(raw_turn_counter, int):
            self.turn_counter = max(0, raw_turn_counter)
        self.repository.log_session_event(
            slot=slot,
            event_name="load_command",
            details={"current_room": self.player.current_room, "turn_counter": self.turn_counter},
        )
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
        if self.repository is not None:
            try:
                self.repository.log_session_event(
                    slot="runtime",
                    event_name="shutdown",
                    details={"current_room": self.player.current_room, "turn_counter": self.turn_counter},
                )
            except DatabaseError:
                pass
        self.repository.close()

    def loop_delay(self) -> None:
        """Small pause to preserve the original game's pacing."""
        time.sleep(self.sleep_seconds)

    def reset(self) -> None:
        """Reset in-memory game state for a fresh run."""
        try:
            self.repository.log_session_event(
                slot="runtime",
                event_name="reset",
                details={"current_room": self.player.current_room, "turn_counter": self.turn_counter},
            )
        except DatabaseError:
            pass
        self.rooms = self._build_rooms()
        self.world = self._build_world_graph(self.rooms)
        self.room_lookup = {_normalize_text(name): name for name in self.rooms}
        self.item_lookup = self._build_item_lookup(self.rooms)
        self.player = Player(current_room="Garden", inventory=Inventory())
        self.enemy_profile = self._build_default_enemy_profile()
        self.combat = CombatSystem(required_item_count=self.required_items, enemy_profile=self.enemy_profile)
        self.event_queue = EventQueue()
        self.turn_counter = 0
        self.is_running = True
