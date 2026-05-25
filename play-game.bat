@echo off
setlocal

REM Run from this script's directory so paths always resolve correctly.
cd /d "%~dp0"

echo ========================================
echo Haunted Mansion Escape Launcher
echo ========================================
echo.

REM Create virtual environment if missing.
if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment...
    py -m venv .venv
    if errorlevel 1 (
        echo Failed to create virtual environment.
        echo Make sure Python is installed and available as "py".
        pause
        exit /b 1
    )
)

REM Start MongoDB container for save/load support.
echo Ensuring MongoDB is running...
docker --version >nul 2>&1
if errorlevel 1 (
    echo Docker is not available. Continuing without auto-starting MongoDB.
    echo Save/load may be disabled unless MongoDB is running locally.
) else (
    docker compose up -d mongodb >nul 2>&1
    if errorlevel 1 (
        echo Unable to start MongoDB with Docker Compose.
        echo Continuing launch, but save/load may be disabled.
    ) else (
        echo MongoDB container is running.
    )
)

REM Install/update dependencies.
echo Installing dependencies...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    echo Failed to install dependencies.
    pause
    exit /b 1
)

REM Start the game in CLI mode.
echo.
echo Starting game...
echo.
".venv\Scripts\python.exe" main.py --mode cli
set EXIT_CODE=%ERRORLEVEL%

echo.
echo Game exited with code %EXIT_CODE%.
pause
exit /b %EXIT_CODE%
