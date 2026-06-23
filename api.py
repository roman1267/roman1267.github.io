"""Lightweight API layer for online functionality."""

from __future__ import annotations
# pyright: reportUnusedFunction=false

import importlib
import logging
from datetime import datetime
from typing import Any, Dict, cast

from game.database import DatabaseError
from game.game_engine import GameEngine


logger = logging.getLogger(__name__)


def create_app(engine: GameEngine) -> Any:
    """Create a Flask app exposing game state and save operations."""
    try:
        flask_module = importlib.import_module("flask")
    except Exception as exc:
        raise RuntimeError(
            "Flask is not installed. Install dependencies from requirements.txt."
        ) from exc

    flask_class = getattr(flask_module, "Flask")
    request = getattr(flask_module, "request")
    app: Any = flask_class(__name__, static_folder="web", static_url_path="/web")

    def _parse_limit(raw_limit: Any, default: int, max_limit: int) -> int:
        try:
            parsed = int(raw_limit)
        except (TypeError, ValueError):
            return default
        return max(1, min(parsed, max_limit))

    def _to_json_compatible(value: Any) -> Any:
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, list):
            return [_to_json_compatible(item) for item in value]
        if isinstance(value, dict):
            return {str(key): _to_json_compatible(item) for key, item in value.items()}
        return value

    @app.get("/")
    def index() -> Any:
        return app.send_static_file("index.html")

    @app.get("/health")
    def health() -> tuple[Dict[str, str], int]:
        logger.debug("GET /health")
        return {"status": "ok"}, 200

    @app.get("/state")
    def state() -> tuple[Dict[str, Any], int]:
        logger.debug("GET /state room=%s", engine.player.current_room)
        room = engine.rooms[engine.player.current_room]
        return (
            {
                "current_room": engine.player.current_room,
                "inventory": engine.player.inventory.to_list(),
                "room_item": room.item,
                "exits": room.exits,
            },
            200,
        )

    @app.post("/command")
    def command() -> tuple[Dict[str, Any], int]:
        payload_raw = request.get_json(silent=True)
        payload: Dict[str, Any] = {}
        if isinstance(payload_raw, dict):
            raw_dict = cast(Dict[Any, Any], payload_raw)
            for key, value in raw_dict.items():
                payload[str(key)] = value
        raw = str(payload.get("command", "")).strip()
        if not raw:
            logger.warning("POST /command missing command payload")
            return {"error": "command is required"}, 400

        logger.info("POST /command command=%s", raw)
        message = engine.process_command(raw)
        return {"message": message, "running": engine.is_running}, 200

    @app.post("/save/<slot>")
    def save(slot: str) -> tuple[Dict[str, str], int]:
        logger.info("POST /save slot=%s", slot)
        message = engine.process_command(f"save {slot}")
        return {"message": message}, 200

    @app.get("/saves")
    def saves() -> tuple[Dict[str, str], int]:
        logger.debug("GET /saves")
        message = engine.process_command("saves")
        return {"message": message}, 200

    @app.post("/reset")
    def reset() -> tuple[Dict[str, str], int]:
        logger.info("POST /reset")
        engine.reset()
        return {"message": "New game started."}, 200

    @app.get("/admin/rooms")
    def admin_rooms() -> tuple[Dict[str, Any], int]:
        logger.debug("GET /admin/rooms")
        try:
            rooms = engine.repository.list_room_configs()
        except DatabaseError as exc:
            logger.warning("GET /admin/rooms failed: %s", exc)
            return {"error": str(exc)}, 503
        return {"rooms": _to_json_compatible(rooms), "count": len(rooms)}, 200

    @app.get("/admin/enemies")
    def admin_enemies() -> tuple[Dict[str, Any], int]:
        logger.debug("GET /admin/enemies")
        try:
            enemies = engine.repository.list_enemy_configs()
        except DatabaseError as exc:
            logger.warning("GET /admin/enemies failed: %s", exc)
            return {"error": str(exc)}, 503
        return {"enemies": _to_json_compatible(enemies), "count": len(enemies)}, 200

    @app.get("/admin/sessions")
    def admin_sessions() -> tuple[Dict[str, Any], int]:
        slot = str(request.args.get("slot", "")).strip() or None
        event_name = str(request.args.get("event_name", "")).strip() or None
        limit = _parse_limit(request.args.get("limit"), default=100, max_limit=500)
        logger.debug("GET /admin/sessions slot=%s event_name=%s limit=%s", slot, event_name, limit)
        try:
            sessions = engine.repository.list_session_events(slot=slot, event_name=event_name, limit=limit)
        except DatabaseError as exc:
            logger.warning("GET /admin/sessions failed: %s", exc)
            return {"error": str(exc)}, 503
        return {"sessions": _to_json_compatible(sessions), "count": len(sessions)}, 200

    @app.get("/admin/replay/<slot>")
    def admin_replay(slot: str) -> tuple[Dict[str, Any], int]:
        cleaned_slot = slot.strip()
        if not cleaned_slot:
            return {"error": "slot is required"}, 400

        limit = _parse_limit(request.args.get("limit"), default=200, max_limit=1000)
        logger.debug("GET /admin/replay/%s limit=%s", cleaned_slot, limit)
        try:
            timeline = engine.repository.replay_actions(cleaned_slot, limit=limit)
        except DatabaseError as exc:
            logger.warning("GET /admin/replay/%s failed: %s", cleaned_slot, exc)
            return {"error": str(exc)}, 503
        return {
            "slot": cleaned_slot,
            "timeline": _to_json_compatible(timeline),
            "count": len(timeline),
        }, 200

    return app
