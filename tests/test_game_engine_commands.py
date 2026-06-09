from game.game_engine import GameEngine


def test_command_alias_and_item_lookup() -> None:
    engine = GameEngine(sleep_seconds=0)

    move_result = engine.process_command("move east")
    pickup_result = engine.process_command("get crystal orb")

    assert "You move East into the Entrance Hall." in move_result
    assert pickup_result == "Crystal Orb retrieved."


def test_route_command_and_invalid_command_handling() -> None:
    engine = GameEngine(sleep_seconds=0)

    route_result = engine.process_command("route Attic")
    bad_result = engine.process_command("teleport attic")

    assert "Shortest route to Attic" in route_result
    assert "Invalid command" in bad_result
