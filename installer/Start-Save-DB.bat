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

set "CONTAINER_NAME=haunted-mansion-mongo"

docker ps -a --format "{{.Names}}" | findstr /I /X "%CONTAINER_NAME%" >nul
if errorlevel 1 (
    docker run -d --name %CONTAINER_NAME% -p 27017:27017 --restart unless-stopped mongo:7
    if errorlevel 1 (
        echo Could not create and start MongoDB container.
        echo Make sure Docker Desktop is running and the port 27017 is available.
        pause
        exit /b 1
    )
) else (
    docker start %CONTAINER_NAME% >nul
    if errorlevel 1 (
        echo Could not start existing MongoDB container.
        echo Make sure Docker Desktop is running.
        pause
        exit /b 1
    )
)

echo MongoDB container "%CONTAINER_NAME%" is running on localhost:27017.
echo Save/load is now available in game.
pause
