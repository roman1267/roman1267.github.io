# CS-499 - Category One: Software Design and Engineering

This repository contains an enhanced version of a text-based adventure game originally built for IT-140. The project was refactored from a monolithic script into a modular, object-oriented architecture with MongoDB persistence, a lightweight API layer, and Docker support.

## Enhancement Summary

- Refactored procedural logic into classes and domain modules
- Introduced a centralized game engine
- Added improved command parsing, validation, and error handling
- Implemented configurable room and item management
- Added MongoDB-backed save/load functionality
- Added optional API mode for online interaction
- Added Docker and Docker Compose for containerized execution

## Project Structure

- `TextBasedGame.py` - legacy launcher that starts the new architecture
- `main.py` - application entrypoint (`cli` or `api` mode)
- `game_engine.py` - core orchestration and command processing
- `player.py` - player model
- `room.py` - room model and movement rules
- `inventory.py` - inventory model
- `combat.py` - encounter resolution
- `database.py` - MongoDB persistence layer
- `api.py` - Flask API endpoints
- `requirements.txt` - Python dependencies
- `Dockerfile` / `docker-compose.yml` - container setup

## Requirements

- Python 3.11+
- MongoDB (local instance or container)

## Local Run (CLI)

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Set MongoDB URI (optional if using local default):

```bash
set MONGODB_URI=mongodb://localhost:27017
```

3. Run game:

```bash
python main.py --mode cli
```

You can also continue using:

```bash
python TextBasedGame.py
```

## API Run

```bash
python main.py --mode api --host 0.0.0.0 --port 8000
```

### API Endpoints

- `GET /health` - service health
- `GET /state` - current game state
- `POST /command` - execute command, JSON body: `{ "command": "go East" }`
- `POST /save/<slot>` - save to slot
- `GET /saves` - list save slots

## Docker Run

Run game and MongoDB together:

```bash
docker compose up --build
```

This starts:

- `mongodb` on port `27017`
- `game` container in CLI mode

## Core Commands In Game

- `go <North|South|East|West>`
- `get <item name>`
- `inventory`
- `save [slot]`
- `load [slot]`
- `saves`
- `help`
- `quit`

## Course Outcome Alignment

This enhancement demonstrates:

- object-oriented software design
- modular software engineering
- maintainability and separation of concerns
- persistence integration with MongoDB
- API integration fundamentals
- containerized deployment with Docker
