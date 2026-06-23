from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from api import create_app
from game.database import DatabaseError
from game.game_engine import GameEngine


class FakeRepository:
    def __init__(self) -> None:
        self.sessions_call: Optional[tuple[Optional[str], Optional[str], int, bool]] = None
        self.replay_call: Optional[tuple[str, int]] = None

    def list_room_configs(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "Garden",
                "exits": {"East": "Entrance Hall"},
                "item": None,
                "updated_at": datetime(2026, 6, 22, 12, 0, tzinfo=timezone.utc),
            }
        ]

    def list_enemy_configs(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "Phantom of Despair",
                "room": "Attic",
                "base_hp": 28,
                "base_attack": 9,
                "base_defense": 5,
                "item_attack_bonuses": {"Silver Knife": 4},
                "item_defense_bonuses": {"Key": 1},
                "updated_at": datetime(2026, 6, 22, 12, 0, tzinfo=timezone.utc),
            }
        ]

    def list_session_events(
        self,
        slot: Optional[str] = None,
        event_name: Optional[str] = None,
        limit: int = 100,
        sort_ascending: bool = False,
    ) -> list[dict[str, Any]]:
        self.sessions_call = (slot, event_name, limit, sort_ascending)
        return [
            {
                "slot": slot or "runtime",
                "event_name": event_name or "move",
                "details": {"room": "Garden"},
                "updated_at": datetime(2026, 6, 22, 12, 1, tzinfo=timezone.utc),
            }
        ]

    def replay_actions(self, slot: str, limit: int = 200) -> list[dict[str, Any]]:
        self.replay_call = (slot, limit)
        return [
            {
                "slot": slot,
                "event_name": "save_command",
                "details": {"current_room": "Garden"},
                "updated_at": datetime(2026, 6, 22, 12, 2, tzinfo=timezone.utc),
            }
        ]


class FailingRepository:
    def list_room_configs(self) -> list[dict[str, Any]]:
        raise DatabaseError("Database is not connected.")


def _build_test_client(repository: Any) -> Any:
    engine = GameEngine(sleep_seconds=0)
    engine.repository = repository
    app = create_app(engine)
    return app.test_client()


def test_admin_rooms_returns_room_configs() -> None:
    client = _build_test_client(FakeRepository())

    response = client.get("/admin/rooms")
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["count"] == 1
    assert payload["rooms"][0]["name"] == "Garden"
    assert isinstance(payload["rooms"][0]["updated_at"], str)


def test_admin_enemies_returns_enemy_configs() -> None:
    client = _build_test_client(FakeRepository())

    response = client.get("/admin/enemies")
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["count"] == 1
    assert payload["enemies"][0]["name"] == "Phantom of Despair"


def test_admin_sessions_uses_query_parameters() -> None:
    repository = FakeRepository()
    client = _build_test_client(repository)

    response = client.get("/admin/sessions?slot=alpha&event_name=move&limit=25")
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["count"] == 1
    assert repository.sessions_call == ("alpha", "move", 25, False)


def test_admin_replay_returns_timeline_for_slot() -> None:
    repository = FakeRepository()
    client = _build_test_client(repository)

    response = client.get("/admin/replay/alpha?limit=40")
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["slot"] == "alpha"
    assert payload["count"] == 1
    assert repository.replay_call == ("alpha", 40)


def test_admin_rooms_returns_503_when_database_unavailable() -> None:
    client = _build_test_client(FailingRepository())

    response = client.get("/admin/rooms")
    payload = response.get_json()

    assert response.status_code == 503
    assert "Database is not connected" in payload["error"]
