"""Application entrypoint for CLI and optional API runtime."""

from __future__ import annotations

import argparse

from game_engine import GameEngine


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
    args = parse_args()
    engine = GameEngine()

    if args.mode == "api":
        run_api(engine, host=args.host, port=args.port)
        return

    run_cli(engine)


if __name__ == "__main__":
    main()
