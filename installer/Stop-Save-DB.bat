@echo off
setlocal
cd /d "%~dp0"

echo Stopping MongoDB save/load container...
where docker >nul 2>nul
if errorlevel 1 (
    echo Docker is not installed or not on PATH.
    pause
    exit /b 1
)

docker compose stop mongodb
if errorlevel 1 (
    echo Could not stop MongoDB container.
    echo Make sure Docker Desktop is running.
    pause
    exit /b 1
)

echo MongoDB container stopped.
pause
