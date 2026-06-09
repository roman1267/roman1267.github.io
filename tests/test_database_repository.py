from database import MongoGameRepository
from room import Room


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
