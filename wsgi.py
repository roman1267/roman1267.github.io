"""WSGI entrypoint for production API serving."""

from __future__ import annotations

import logging
import os

from game.game_engine import GameEngine
from api import create_app


def configure_logging() -> None:
	"""Configure logging for gunicorn/WSGI execution paths."""
	level_name = os.getenv("LOG_LEVEL", "INFO").upper()
	level = getattr(logging, level_name, logging.INFO)
	logging.basicConfig(
		level=level,
		format="%(asctime)s %(levelname)s %(name)s: %(message)s",
	)

configure_logging()
engine = GameEngine(sleep_seconds=0)
engine.initialize()
app = create_app(engine)
