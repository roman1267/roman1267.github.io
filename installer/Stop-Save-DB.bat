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

set "CONTAINER_NAME=haunted-mansion-mongo"

docker ps -a --format "{{.Names}}" | findstr /I /X "%CONTAINER_NAME%" >nul
if errorlevel 1 (
    echo MongoDB container "%CONTAINER_NAME%" was not found.
    pause
    exit /b 0
)

docker stop %CONTAINER_NAME% >nul
if errorlevel 1 (
    echo Could not stop MongoDB container.
    echo Make sure Docker Desktop is running.
    pause
    exit /b 1
)

echo MongoDB container "%CONTAINER_NAME%" stopped.
pause
