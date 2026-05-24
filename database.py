"""MongoDB persistence layer for game state."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from player import Player


class DatabaseError(Exception):
    """Raised when game state persistence fails."""


class MongoGameRepository:
    """Stores and loads save slots in MongoDB."""

    def __init__(
        self,
        uri: Optional[str] = None,
        database_name: str = "haunted_mansion",
        collection_name: str = "saves",
    ) -> None:
        self.uri = uri or os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        self.database_name = database_name
        self.collection_name = collection_name
        self._client = None
        self._collection = None

    def connect(self) -> None:
        """Create MongoDB client and validate connectivity."""
        try:
            from pymongo import MongoClient
            from pymongo.errors import PyMongoError
        except Exception as exc:
            raise DatabaseError(
                "PyMongo is not installed. Install dependencies from requirements.txt."
            ) from exc

        try:
            self._client = MongoClient(
                self.uri,
                maxPoolSize=20,
                minPoolSize=0,
                maxIdleTimeMS=300000,
                connectTimeoutMS=5000,
                serverSelectionTimeoutMS=5000,
            )
            self._client.admin.command("ping")
            self._collection = self._client[self.database_name][self.collection_name]
        except PyMongoError as exc:
            raise DatabaseError(f"Unable to connect to MongoDB: {exc}") from exc

    def save_game(self, slot: str, player: Player) -> None:
        """Persist game state to a named save slot."""
        if self._collection is None:
            raise DatabaseError("Database is not connected.")

        payload: Dict[str, Any] = {
            "slot": slot,
            "player": {
                "current_room": player.current_room,
                "inventory": player.inventory.to_list(),
            },
            "updated_at": datetime.now(timezone.utc),
        }

        self._collection.update_one({"slot": slot}, {"$set": payload}, upsert=True)

    def load_game(self, slot: str) -> Optional[Dict[str, Any]]:
        """Load game state from a named slot. Returns None if not found."""
        if self._collection is None:
            raise DatabaseError("Database is not connected.")

        data = self._collection.find_one({"slot": slot}, {"_id": 0})
        return data

    def list_saves(self) -> list[Dict[str, Any]]:
        """List available save slots."""
        if self._collection is None:
            raise DatabaseError("Database is not connected.")

        return list(
            self._collection.find({}, {"_id": 0, "slot": 1, "updated_at": 1}).sort(
                "updated_at", -1
            )
        )

    def close(self) -> None:
        """Close MongoDB client."""
        if self._client is not None:
            self._client.close()
            self._client = None
            self._collection = None
