@echo off
setlocal
cd /d "%~dp0"

echo Starting MongoDB for save/load support using Docker...
where docker >nul 2>nul
if errorlevel 1 (
    echo Docker is not installed or not on PATH.
    echo Install Docker Desktop, then run this script again.
    pause
    exit /b 1
)

docker compose up -d mongodb
if errorlevel 1 (
    echo Could not start MongoDB container.
    echo Make sure Docker Desktop is running.
    pause
    exit /b 1
)

echo MongoDB started. Save/load is now available in game.
pause
