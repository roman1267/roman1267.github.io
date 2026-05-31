@echo off
setlocal

REM Run from this script's directory so paths always resolve correctly.
cd /d "%~dp0"

echo ========================================
echo Haunted Mansion Escape Launcher
echo ========================================
echo.

set "RUN_MODE="
if /I "%~1"=="cli" set "RUN_MODE=cli"
if /I "%~1"=="web" set "RUN_MODE=web"
if /I "%~1"=="ui" set "RUN_MODE=web"

if not defined RUN_MODE (
    echo Select launch mode:
    echo   [1] Browser UI (recommended)
    echo   [2] CLI
    set /p MODE_CHOICE=Enter choice [1/2, default 1]: 
    if "%MODE_CHOICE%"=="2" (
        set "RUN_MODE=cli"
    ) else (
        set "RUN_MODE=web"
    )
)

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

if /I "%RUN_MODE%"=="web" goto :RUN_WEB

REM Start the game in CLI mode.
:RUN_CLI
echo.
echo Starting game in CLI mode...
echo.
".venv\Scripts\python.exe" main.py --mode cli
set EXIT_CODE=%ERRORLEVEL%
goto :END

REM Start the game in API mode and open browser UI.
:RUN_WEB
echo.
echo Starting Browser UI at http://localhost:8000/
echo Press Ctrl+C in this window to stop the server.
echo.
start "" "http://localhost:8000/"
".venv\Scripts\python.exe" main.py --mode api --host 0.0.0.0 --port 8000
set EXIT_CODE=%ERRORLEVEL%

:END
echo.
echo Game exited with code %EXIT_CODE%.
pause
exit /b %EXIT_CODE%
