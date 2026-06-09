"""Application entrypoint for CLI and optional API runtime."""

from __future__ import annotations

import argparse
import logging
import os

from game.game_engine import GameEngine


def configure_logging() -> None:
    """Configure application logging for local and deployed runtimes."""
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def run_cli(engine: GameEngine) -> None:
    """Run the text-based interactive game loop."""
    print(engine.initialize())
    print("Type 'help' for available commands.")

    try:
        while engine.is_running:
            engine.loop_delay()
            print(engine.format_status())
            raw = input("\n> Enter command: ").strip()
            message = engine.process_command(raw)
            print(f"\n> {message}\n")
    finally:
        engine.shutdown()


def run_api(engine: GameEngine, host: str, port: int) -> None:
    """Run the lightweight HTTP API."""
    print(engine.initialize())

    from api import create_app

    app = create_app(engine)
    try:
        app.run(host=host, port=port)
    finally:
        engine.shutdown()


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for runtime mode."""
    parser = argparse.ArgumentParser(description="Haunted Mansion Escape")
    parser.add_argument(
        "--mode",
        choices=["cli", "api"],
        default="cli",
        help="Run interactive CLI or HTTP API mode.",
    )
    parser.add_argument("--host", default="0.0.0.0", help="API host binding")
    parser.add_argument("--port", default=8000, type=int, help="API port")
    return parser.parse_args()


def main() -> None:
    """Program bootstrap."""
    configure_logging()
    args = parse_args()
    engine = GameEngine()

    if args.mode == "api":
        run_api(engine, host=args.host, port=args.port)
        return

    run_cli(engine)


if __name__ == "__main__":
    main()
