"""Lightweight API layer for online functionality."""

from __future__ import annotations
# pyright: reportUnusedFunction=false

import importlib
import logging
from typing import Any, Dict, cast

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

    return app
