from __future__ import annotations

import os

import pytest

from database import MongoGameRepository
from inventory import Inventory
from player import Player
from room import Room


pytestmark = pytest.mark.integration


def _get_test_uri() -> str:
    uri = os.getenv("MONGODB_URI", "").strip()
    if not uri:
        pytest.skip("MONGODB_URI is not set; skipping MongoDB integration test.")
    return uri


def test_repository_round_trip_with_real_mongo() -> None:
    uri = _get_test_uri()
    repository = MongoGameRepository(uri=uri, database_name="haunted_mansion_test")
    repository.connect()

    try:
        default_rooms = {
            "Garden": Room(name="Garden", exits={"East": "Entrance Hall"}, item=None),
            "Entrance Hall": Room(name="Entrance Hall", exits={"West": "Garden"}, item="Crystal Orb"),
        }

        loaded_rooms = repository.load_or_seed_rooms(default_rooms)
        assert "Garden" in loaded_rooms
        assert "Entrance Hall" in loaded_rooms

        player = Player(current_room="Garden", inventory=Inventory.from_iterable(["Crystal Orb", "Key"]))
        repository.save_game("integration", player, turn_counter=3)

        loaded = repository.load_game("integration")
        assert loaded is not None
        assert loaded["slot"] == "integration"
        assert loaded["player"]["current_room"] == "Garden"
        assert loaded["player"]["inventory"] == ["Crystal Orb", "Key"]
        assert loaded["turn_counter"] == 3

        saves = repository.list_saves()
        assert any(save.get("slot") == "integration" for save in saves)
    finally:
        if repository._client is not None:
            repository._client.drop_database("haunted_mansion_test")
        repository.close()