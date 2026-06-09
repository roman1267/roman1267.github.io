from game.game_engine import GameEngine


def test_shortest_path_from_garden_to_attic() -> None:
    engine = GameEngine(sleep_seconds=0)

    directions = engine.world.shortest_path_directions("Garden", "Attic")
    rooms = engine.world.shortest_path_rooms("Garden", "Attic")

    assert directions == ["East", "East", "North"]
    assert rooms == ["Garden", "Entrance Hall", "Master Bedroom", "Attic"]


def test_world_can_move_and_next_room() -> None:
    engine = GameEngine(sleep_seconds=0)

    assert engine.world.can_move("Garden", "East") is True
    assert engine.world.next_room("Garden", "East") == "Entrance Hall"
    assert engine.world.can_move("Garden", "North") is False
    assert engine.world.next_room("Garden", "North") is None
