import pytest

from game.database import DatabaseError, MongoGameRepository
from game.game_engine import GameEngine
from game.inventory import Inventory
from game.player import Player
from game.room import Room


def test_load_or_seed_rooms_seeds_when_empty() -> None:
    repository = MongoGameRepository()

    class FakeRoomsCollection:
        def __init__(self) -> None:
            self.inserted = None

        def find(self, *_args, **_kwargs):
            return []

        def insert_many(self, documents):
            self.inserted = documents

    fake_collection = FakeRoomsCollection()
    repository._rooms = fake_collection

    default_rooms = {
        "Garden": Room(name="Garden", exits={"East": "Entrance Hall"}, item=None),
        "Entrance Hall": Room(name="Entrance Hall", exits={"West": "Garden"}, item="Crystal Orb"),
    }

    loaded = repository.load_or_seed_rooms(default_rooms)

    assert loaded is default_rooms
    assert fake_collection.inserted is not None
    assert len(fake_collection.inserted) == 2
    room_names = {doc["name"] for doc in fake_collection.inserted}
    assert room_names == {"Garden", "Entrance Hall"}


def test_load_or_seed_rooms_rehydrates_room_objects() -> None:
    repository = MongoGameRepository()

    class FakeRoomsCollection:
        def find(self, *_args, **_kwargs):
            return [
                {
                    "name": "Garden",
                    "exits": {"East": "Entrance Hall"},
                    "item": None,
                },
                {
                    "name": "Entrance Hall",
                    "exits": {"West": "Garden"},
                    "item": "Crystal Orb",
                },
            ]

        def insert_many(self, _documents):
            raise AssertionError("insert_many should not be called when rooms exist")

    repository._rooms = FakeRoomsCollection()

    loaded = repository.load_or_seed_rooms(default_rooms={})

    assert loaded["Garden"].exits == {"East": "Entrance Hall"}
    assert loaded["Entrance Hall"].item == "Crystal Orb"


def test_load_or_seed_enemy_seeds_when_missing() -> None:
    repository = MongoGameRepository()

    class FakeEnemiesCollection:
        def __init__(self) -> None:
            self.upserted = None

        def find_one(self, *_args, **_kwargs):
            return None

        def update_one(self, filter_doc, update_doc, upsert=False):
            self.upserted = (filter_doc, update_doc, upsert)

    fake_collection = FakeEnemiesCollection()
    repository._enemies = fake_collection

    default_enemy = {
        "name": "Phantom of Despair",
        "room": "Attic",
        "base_hp": 28,
        "base_attack": 9,
        "base_defense": 5,
        "item_attack_bonuses": {"Silver Knife": 4},
        "item_defense_bonuses": {"Key": 1},
    }

    enemy_doc = repository.load_or_seed_enemy(default_enemy)

    assert enemy_doc["name"] == "Phantom of Despair"
    assert fake_collection.upserted is not None
    assert fake_collection.upserted[0] == {"name": "Phantom of Despair"}
    assert fake_collection.upserted[2] is True


def test_enemy_profile_can_be_loaded_from_persisted_doc() -> None:
    engine = GameEngine(sleep_seconds=0)

    enemy_doc = {
        "name": "Wraith King",
        "room": "Attic",
        "base_hp": 40,
        "base_attack": 11,
        "base_defense": 7,
        "item_attack_bonuses": {"Crystal Orb": 5},
        "item_defense_bonuses": {"Lantern of Shadows": 4},
    }

    profile = engine._enemy_profile_from_doc(enemy_doc)

    assert profile.name == "Wraith King"
    assert profile.room == "Attic"
    assert profile.base_hp == 40
    assert profile.item_attack_bonuses["Crystal Orb"] == 5
    assert profile.item_defense_bonuses["Lantern of Shadows"] == 4


def test_save_game_rejects_invalid_slot_before_persistence() -> None:
    repository = MongoGameRepository()

    class FakePlayersCollection:
        def update_one(self, *_args, **_kwargs):
            raise AssertionError("update_one should not run for invalid payloads")

    class FakeInventoryCollection:
        def update_one(self, *_args, **_kwargs):
            raise AssertionError("update_one should not run for invalid payloads")

    class FakeStateCollection:
        def update_one(self, *_args, **_kwargs):
            raise AssertionError("update_one should not run for invalid payloads")

    repository._players = FakePlayersCollection()
    repository._inventory = FakeInventoryCollection()
    repository._game_state = FakeStateCollection()

    player = Player(current_room="Garden", inventory=Inventory())

    with pytest.raises(DatabaseError, match="Invalid player document"):
        repository.save_game("   ", player)
