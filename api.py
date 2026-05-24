"""Lightweight API layer for online functionality."""

from __future__ import annotations

from typing import Any, Dict

from game_engine import GameEngine


def create_app(engine: GameEngine):
    """Create a Flask app exposing game state and save operations."""
    try:
        from flask import Flask, jsonify, request
    except Exception as exc:
        raise RuntimeError(
            "Flask is not installed. Install dependencies from requirements.txt."
        ) from exc

    app = Flask(__name__)

    @app.get("/health")
    def health() -> tuple[Dict[str, str], int]:
        return {"status": "ok"}, 200

    @app.get("/state")
    def state() -> tuple[Dict[str, Any], int]:
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
        payload = request.get_json(silent=True) or {}
        raw = str(payload.get("command", "")).strip()
        if not raw:
            return {"error": "command is required"}, 400

        message = engine.process_command(raw)
        return {"message": message, "running": engine.is_running}, 200

    @app.post("/save/<slot>")
    def save(slot: str) -> tuple[Dict[str, str], int]:
        message = engine.process_command(f"save {slot}")
        return {"message": message}, 200

    @app.get("/saves")
    def saves() -> tuple[Dict[str, str], int]:
        message = engine.process_command("saves")
        return {"message": message}, 200

    return app
