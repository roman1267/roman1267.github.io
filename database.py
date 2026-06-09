"""MongoDB persistence layer for game state."""

from __future__ import annotations

import os
from importlib import import_module
from datetime import datetime, timezone
from typing import Any, Dict, Optional, cast

from player import Player
from room import Room


class DatabaseError(Exception):
    """Raised when game state persistence fails."""


class MongoGameRepository:
    """Stores and loads game state using multiple MongoDB collections."""

    def __init__(
        self,
        uri: Optional[str] = None,
        database_name: str = "haunted_mansion",
    ) -> None:
        self.uri = uri or os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        self.database_name = database_name
        self._client: Any | None = None
        self._players: Any | None = None
        self._inventory: Any | None = None
        self._rooms: Any | None = None
        self._enemies: Any | None = None
        self._game_state: Any | None = None
        self._sessions: Any | None = None

    @staticmethod
    def _utc_now() -> datetime:
        """Return timezone-aware UTC datetime for persistence timestamps."""
        return datetime.now(timezone.utc)

    def connect(self) -> None:
        """Create MongoDB client and validate connectivity."""
        try:
            pymongo_module = import_module("pymongo")
            pymongo_errors = import_module("pymongo.errors")
            mongo_client_ctor = getattr(pymongo_module, "MongoClient")
            pymongo_error_type = getattr(pymongo_errors, "PyMongoError")
        except Exception as exc:
            raise DatabaseError(
                "PyMongo is not installed. Install dependencies from requirements.txt."
            ) from exc

        try:
            self._client = mongo_client_ctor(
                self.uri,
                maxPoolSize=20,
                minPoolSize=0,
                maxIdleTimeMS=300000,
                connectTimeoutMS=5000,
                serverSelectionTimeoutMS=5000,
            )
            if self._client is None:
                raise DatabaseError("MongoDB client initialization failed.")
            self._client.admin.command("ping")
            database = self._client[self.database_name]
            self._players = database["players"]
            self._inventory = database["inventory"]
            self._rooms = database["rooms"]
            self._enemies = database["enemies"]
            self._game_state = database["game_state"]
            self._sessions = database["game_sessions"]
            self._create_indexes()
        except pymongo_error_type as exc:
            raise DatabaseError(f"Unable to connect to MongoDB: {exc}") from exc

    def _create_indexes(self) -> None:
        """Create collection indexes used for fast save/load lookups."""
        if (
            self._players is None
            or self._inventory is None
            or self._rooms is None
            or self._enemies is None
            or self._game_state is None
            or self._sessions is None
        ):
            raise DatabaseError("Database is not connected.")

        self._players.create_index("slot", unique=True)
        self._inventory.create_index("slot", unique=True)
        self._rooms.create_index("name", unique=True)
        self._enemies.create_index("name", unique=True)
        self._game_state.create_index("slot", unique=True)
        self._sessions.create_index([("slot", 1), ("updated_at", -1)])
        self._sessions.create_index("updated_at", expireAfterSeconds=60 * 60 * 24 * 30)

    def load_or_seed_rooms(self, default_rooms: Dict[str, Room]) -> Dict[str, Room]:
        """Load room documents from MongoDB or seed defaults if absent."""
        if self._rooms is None:
            raise DatabaseError("Database is not connected.")

        room_docs = list(self._rooms.find({}, {"_id": 0}))
        if not room_docs:
            now = self._utc_now()
            seed_docs = [
                {
                    "name": room.name,
                    "exits": room.exits,
                    "item": room.item,
                    "updated_at": now,
                }
                for room in default_rooms.values()
            ]
            if seed_docs:
                self._rooms.insert_many(seed_docs)
            return default_rooms

        loaded_rooms: Dict[str, Room] = {}
        for doc in room_docs:
            name = str(doc.get("name", "")).strip()
            if not name:
                continue

            raw_exits = doc.get("exits", {})
            exits: dict[str, str] = {}
            if isinstance(raw_exits, dict):
                exits = {str(key): str(value) for key, value in raw_exits.items()}

            item = doc.get("item")
            loaded_rooms[name] = Room(name=name, exits=exits, item=str(item) if item else None)

        if not loaded_rooms:
            return default_rooms
        return loaded_rooms

    def load_or_seed_enemy(self, default_enemy: Dict[str, Any]) -> Dict[str, Any]:
        """Load the primary enemy document from MongoDB or seed a default profile."""
        if self._enemies is None:
            raise DatabaseError("Database is not connected.")

        enemy_doc = self._enemies.find_one({"name": default_enemy.get("name")}, {"_id": 0})
        if not isinstance(enemy_doc, dict):
            seed_doc = dict(default_enemy)
            seed_doc["updated_at"] = self._utc_now()
            self._enemies.update_one({"name": seed_doc["name"]}, {"$set": seed_doc}, upsert=True)
            return seed_doc

        return enemy_doc

    def save_game(self, slot: str, player: Player, turn_counter: int = 0) -> None:
        """Persist player, inventory, and game state to a named save slot."""
        if self._players is None or self._inventory is None or self._game_state is None:
            raise DatabaseError("Database is not connected.")

        now = self._utc_now()
        player_payload: Dict[str, Any] = {
            "slot": slot,
            "current_room": player.current_room,
            "updated_at": now,
        }
        inventory_payload: Dict[str, Any] = {
            "slot": slot,
            "items": player.inventory.to_list(),
            "updated_at": now,
        }
        state_payload: Dict[str, Any] = {
            "slot": slot,
            "turn_counter": turn_counter,
            "updated_at": now,
        }

        self._players.update_one({"slot": slot}, {"$set": player_payload}, upsert=True)
        self._inventory.update_one({"slot": slot}, {"$set": inventory_payload}, upsert=True)
        self._game_state.update_one({"slot": slot}, {"$set": state_payload}, upsert=True)

        self.log_session_event(slot=slot, event_name="save", details={"room": player.current_room})

    def load_game(self, slot: str) -> Optional[Dict[str, Any]]:
        """Load a named slot from players/inventory/game_state collections."""
        if self._players is None or self._inventory is None or self._game_state is None:
            raise DatabaseError("Database is not connected.")

        player_doc = self._players.find_one({"slot": slot}, {"_id": 0})
        if not isinstance(player_doc, dict):
            return None

        inventory_doc = self._inventory.find_one({"slot": slot}, {"_id": 0})
        game_state_doc = self._game_state.find_one({"slot": slot}, {"_id": 0})

        inventory_items: list[str] = []
        if isinstance(inventory_doc, dict):
            raw_items = inventory_doc.get("items", [])
            if isinstance(raw_items, list):
                inventory_items = [str(item) for item in raw_items]

        turn_counter = 0
        updated_at = player_doc.get("updated_at")
        if isinstance(game_state_doc, dict):
            raw_turn = game_state_doc.get("turn_counter", 0)
            if isinstance(raw_turn, int):
                turn_counter = raw_turn
            updated_at = game_state_doc.get("updated_at", updated_at)

        payload: Dict[str, Any] = {
            "slot": slot,
            "player": {
                "current_room": player_doc.get("current_room"),
                "inventory": inventory_items,
            },
            "turn_counter": turn_counter,
            "updated_at": updated_at,
        }
        return cast(Dict[str, Any], payload)

    def list_saves(self) -> list[Dict[str, Any]]:
        """List available save slots."""
        if self._game_state is None:
            raise DatabaseError("Database is not connected.")

        return list(
            self._game_state.find({}, {"_id": 0, "slot": 1, "updated_at": 1}).sort(
                "updated_at", -1
            )
        )

    def log_session_event(self, slot: str, event_name: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Store lightweight session events for analytics and future multiplayer features."""
        if self._sessions is None:
            raise DatabaseError("Database is not connected.")

        self._sessions.insert_one(
            {
                "slot": slot,
                "event_name": event_name,
                "details": details or {},
                "updated_at": self._utc_now(),
            }
        )

    def close(self) -> None:
        """Close MongoDB client."""
        if self._client is not None:
            self._client.close()
            self._client = None
            self._players = None
            self._inventory = None
            self._rooms = None
            self._game_state = None
            self._sessions = None
