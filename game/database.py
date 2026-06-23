"""MongoDB persistence layer for game state."""

from __future__ import annotations

import os
from importlib import import_module
from datetime import datetime, timezone
from typing import Any, Dict, Optional, cast

from jsonschema import ValidationError as JsonSchemaValidationError
from jsonschema import validate as validate_json_schema

from .player import Player
from .room import Room


class DatabaseError(Exception):
    """Raised when game state persistence fails."""


PLAYER_DOCUMENT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "required": ["slot", "current_room"],
    "additionalProperties": False,
    "properties": {
        "slot": {"type": "string", "minLength": 1},
        "current_room": {"type": "string", "minLength": 1},
        "updated_at": {},
    },
}

INVENTORY_DOCUMENT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "required": ["slot", "items"],
    "additionalProperties": False,
    "properties": {
        "slot": {"type": "string", "minLength": 1},
        "items": {
            "type": "array",
            "items": {"type": "string", "minLength": 1},
        },
        "updated_at": {},
    },
}

ROOM_DOCUMENT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "required": ["name", "exits"],
    "additionalProperties": False,
    "properties": {
        "name": {"type": "string", "minLength": 1},
        "exits": {
            "type": "object",
            "additionalProperties": {"type": "string", "minLength": 1},
        },
        "item": {"type": ["string", "null"]},
        "updated_at": {},
    },
}

ENEMY_DOCUMENT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "required": ["name", "room", "base_hp", "base_attack", "base_defense"],
    "additionalProperties": False,
    "properties": {
        "name": {"type": "string", "minLength": 1},
        "room": {"type": "string", "minLength": 1},
        "base_hp": {"type": "integer", "minimum": 1},
        "base_attack": {"type": "integer", "minimum": 0},
        "base_defense": {"type": "integer", "minimum": 0},
        "item_attack_bonuses": {
            "type": "object",
            "additionalProperties": {"type": "integer", "minimum": 0},
        },
        "item_defense_bonuses": {
            "type": "object",
            "additionalProperties": {"type": "integer", "minimum": 0},
        },
        "updated_at": {},
    },
}

GAME_STATE_DOCUMENT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "required": ["slot", "turn_counter"],
    "additionalProperties": False,
    "properties": {
        "slot": {"type": "string", "minLength": 1},
        "turn_counter": {"type": "integer", "minimum": 0},
        "updated_at": {},
    },
}

SESSION_EVENT_DOCUMENT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "required": ["slot", "event_name", "details"],
    "additionalProperties": False,
    "properties": {
        "slot": {"type": "string", "minLength": 1},
        "event_name": {"type": "string", "minLength": 1},
        "details": {"type": "object"},
        "updated_at": {},
    },
}

SAVE_SUMMARY_DOCUMENT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "required": ["slot"],
    "additionalProperties": False,
    "properties": {
        "slot": {"type": "string", "minLength": 1},
        "updated_at": {},
    },
}


def _normalize_strings(value: Any) -> Any:
    """Trim whitespace on all nested string values before validation."""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        normalized_items: list[Any] = []
        for item in value:
            normalized_item = _normalize_strings(item)
            if isinstance(normalized_item, str) and not normalized_item:
                continue
            normalized_items.append(normalized_item)
        return normalized_items
    if isinstance(value, dict):
        return {str(key).strip(): _normalize_strings(item) for key, item in value.items()}
    return value

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

    @staticmethod
    def _validate_document(
        payload: Dict[str, Any],
        schema: Dict[str, Any],
        context: str,
        require_updated_at: bool = False,
    ) -> Dict[str, Any]:
        """Validate and normalize payloads with strict schema checks."""
        try:
            normalized_payload = cast(Dict[str, Any], _normalize_strings(payload))
            validate_json_schema(instance=normalized_payload, schema=schema)
            if require_updated_at and not isinstance(normalized_payload.get("updated_at"), datetime):
                raise DatabaseError(f"Invalid {context} document: updated_at must be a datetime")
            return normalized_payload
        except JsonSchemaValidationError as exc:
            raise DatabaseError(f"Invalid {context} document: {exc}") from exc

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
            seed_docs = [
                self._validate_document(
                    {
                    "name": room.name,
                    "exits": room.exits,
                    "item": room.item,
                    "updated_at": self._utc_now(),
                    },
                    ROOM_DOCUMENT_SCHEMA,
                    "room",
                    require_updated_at=True,
                )
                for room in default_rooms.values()
            ]
            if seed_docs:
                self._rooms.insert_many(seed_docs)
            return default_rooms

        loaded_rooms: Dict[str, Room] = {}
        for doc in room_docs:
            room_doc = self._validate_document(doc, ROOM_DOCUMENT_SCHEMA, "room")
            loaded_rooms[room_doc["name"]] = Room(
                name=room_doc["name"],
                exits=cast(dict[str, str], room_doc["exits"]),
                item=cast(Optional[str], room_doc["item"]),
            )

        if not loaded_rooms:
            return default_rooms
        return loaded_rooms

    def load_or_seed_enemy(self, default_enemy: Dict[str, Any]) -> Dict[str, Any]:
        """Load the primary enemy document from MongoDB or seed a default profile."""
        if self._enemies is None:
            raise DatabaseError("Database is not connected.")

        enemy_doc = self._enemies.find_one({"name": default_enemy.get("name")}, {"_id": 0})
        if not isinstance(enemy_doc, dict):
            seed_doc = self._validate_document(
                {**dict(default_enemy), "updated_at": self._utc_now()},
                ENEMY_DOCUMENT_SCHEMA,
                "enemy",
                require_updated_at=True,
            )
            self._enemies.update_one({"name": seed_doc["name"]}, {"$set": seed_doc}, upsert=True)
            return seed_doc

        return self._validate_document(enemy_doc, ENEMY_DOCUMENT_SCHEMA, "enemy")

    def save_game(self, slot: str, player: Player, turn_counter: int = 0) -> None:
        """Persist player, inventory, and game state to a named save slot."""
        if self._players is None or self._inventory is None or self._game_state is None:
            raise DatabaseError("Database is not connected.")

        now = self._utc_now()
        player_payload = self._validate_document(
            {
                "slot": slot,
                "current_room": player.current_room,
                "updated_at": now,
            },
            PLAYER_DOCUMENT_SCHEMA,
            "player",
            require_updated_at=True,
        )
        inventory_payload = self._validate_document(
            {
                "slot": slot,
                "items": player.inventory.to_list(),
                "updated_at": now,
            },
            INVENTORY_DOCUMENT_SCHEMA,
            "inventory",
            require_updated_at=True,
        )
        state_payload = self._validate_document(
            {
                "slot": slot,
                "turn_counter": turn_counter,
                "updated_at": now,
            },
            GAME_STATE_DOCUMENT_SCHEMA,
            "game_state",
            require_updated_at=True,
        )

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
        validated_player_doc = self._validate_document(player_doc, PLAYER_DOCUMENT_SCHEMA, "player")

        inventory_doc = self._inventory.find_one({"slot": slot}, {"_id": 0})
        game_state_doc = self._game_state.find_one({"slot": slot}, {"_id": 0})

        validated_inventory_doc: Dict[str, Any] = {"slot": slot, "items": []}
        if isinstance(inventory_doc, dict):
            validated_inventory_doc = self._validate_document(
                inventory_doc,
                INVENTORY_DOCUMENT_SCHEMA,
                "inventory",
            )

        validated_state_doc: Dict[str, Any] = {
            "slot": slot,
            "turn_counter": 0,
            "updated_at": validated_player_doc.get("updated_at"),
        }
        if isinstance(game_state_doc, dict):
            validated_state_doc = self._validate_document(
                game_state_doc,
                GAME_STATE_DOCUMENT_SCHEMA,
                "game_state",
            )

        payload: Dict[str, Any] = {
            "slot": slot,
            "player": {
                "current_room": validated_player_doc["current_room"],
                "inventory": validated_inventory_doc["items"],
            },
            "turn_counter": validated_state_doc["turn_counter"],
            "updated_at": validated_state_doc.get("updated_at"),
        }
        return cast(Dict[str, Any], payload)

    def list_saves(self) -> list[Dict[str, Any]]:
        """List available save slots."""
        if self._game_state is None:
            raise DatabaseError("Database is not connected.")

        save_docs = list(
            self._game_state.find({}, {"_id": 0, "slot": 1, "updated_at": 1}).sort(
                "updated_at", -1
            )
        )
        return [
            self._validate_document(
                cast(Dict[str, Any], save_doc),
                SAVE_SUMMARY_DOCUMENT_SCHEMA,
                "save_summary",
            )
            for save_doc in save_docs
            if isinstance(save_doc, dict)
        ]

    def list_room_configs(self) -> list[Dict[str, Any]]:
        """Return room configuration documents for admin inspection."""
        if self._rooms is None:
            raise DatabaseError("Database is not connected.")

        room_docs = list(self._rooms.find({}, {"_id": 0}).sort("name", 1))
        return [
            self._validate_document(cast(Dict[str, Any], doc), ROOM_DOCUMENT_SCHEMA, "room")
            for doc in room_docs
            if isinstance(doc, dict)
        ]

    def list_enemy_configs(self) -> list[Dict[str, Any]]:
        """Return enemy configuration documents for admin inspection."""
        if self._enemies is None:
            raise DatabaseError("Database is not connected.")

        enemy_docs = list(self._enemies.find({}, {"_id": 0}).sort("name", 1))
        return [
            self._validate_document(cast(Dict[str, Any], doc), ENEMY_DOCUMENT_SCHEMA, "enemy")
            for doc in enemy_docs
            if isinstance(doc, dict)
        ]

    def list_session_events(
        self,
        slot: Optional[str] = None,
        event_name: Optional[str] = None,
        limit: int = 100,
        sort_ascending: bool = False,
    ) -> list[Dict[str, Any]]:
        """Return persisted session events with optional filters for analytics."""
        if self._sessions is None:
            raise DatabaseError("Database is not connected.")

        cleaned_limit = max(1, min(limit, 500))
        query: Dict[str, Any] = {}
        if slot is not None and slot.strip():
            query["slot"] = slot.strip()
        if event_name is not None and event_name.strip():
            query["event_name"] = event_name.strip()

        sort_direction = 1 if sort_ascending else -1
        session_docs = list(
            self._sessions.find(query, {"_id": 0})
            .sort("updated_at", sort_direction)
            .limit(cleaned_limit)
        )
        return [
            self._validate_document(cast(Dict[str, Any], doc), SESSION_EVENT_DOCUMENT_SCHEMA, "session_event")
            for doc in session_docs
            if isinstance(doc, dict)
        ]

    def replay_actions(self, slot: str, limit: int = 200) -> list[Dict[str, Any]]:
        """Return a chronological event timeline for a specific save slot."""
        cleaned_slot = slot.strip()
        if not cleaned_slot:
            raise DatabaseError("Replay requires a non-empty slot value.")

        return self.list_session_events(slot=cleaned_slot, limit=limit, sort_ascending=True)

    def log_session_event(self, slot: str, event_name: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Store lightweight session events for analytics and future multiplayer features."""
        if self._sessions is None:
            raise DatabaseError("Database is not connected.")

        session_payload = self._validate_document(
            {
                "slot": slot,
                "event_name": event_name,
                "details": details or {},
                "updated_at": self._utc_now(),
            },
            SESSION_EVENT_DOCUMENT_SCHEMA,
            "session_event",
            require_updated_at=True,
        )
        self._sessions.insert_one(session_payload)

    def close(self) -> None:
        """Close MongoDB client."""
        if self._client is not None:
            self._client.close()
            self._client = None
            self._players = None
            self._inventory = None
            self._rooms = None
            self._enemies = None
            self._game_state = None
            self._sessions = None
