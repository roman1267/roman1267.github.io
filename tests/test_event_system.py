from event_system import EventQueue, GameEvent


def test_event_queue_priority_ordering() -> None:
    queue = EventQueue()
    queue.schedule(GameEvent(priority=2, turn=3, name="a", message="A"))
    queue.schedule(GameEvent(priority=1, turn=3, name="b", message="B"))
    queue.schedule(GameEvent(priority=3, turn=3, name="c", message="C"))

    ready = queue.pop_ready(current_turn=3)

    assert [event.name for event in ready] == ["b", "a", "c"]
    assert queue.size() == 0


def test_event_queue_respects_turn_readiness() -> None:
    queue = EventQueue()
    queue.schedule(GameEvent(priority=1, turn=4, name="future", message="Future"))

    ready = queue.pop_ready(current_turn=3)

    assert ready == []
    assert queue.size() == 1
