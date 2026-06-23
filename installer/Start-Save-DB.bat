@echo off
setlocal
cd /d "%~dp0"

echo Starting MongoDB for save/load support using Docker...

net session >nul 2>nul
if errorlevel 1 (
    echo Requesting administrator privileges...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b 0
)

where docker >nul 2>nul
if errorlevel 1 (
    echo Docker CLI not found. Attempting Docker Desktop install via winget...
    where winget >nul 2>nul
    if errorlevel 1 (
        echo winget is not available on this machine.
        echo Install Docker Desktop manually from https://www.docker.com/products/docker-desktop/
        echo Then run this script again.
        pause
        exit /b 1
    )

    winget install --id Docker.DockerDesktop -e --accept-source-agreements --accept-package-agreements
    if errorlevel 1 (
        echo Automatic Docker install failed.
        echo You can still play in terminal mode without save/load.
        echo For save/load, install Docker Desktop manually and re-run this script.
        pause
        exit /b 1
    )
)

echo Ensuring Docker Desktop is running...
docker version >nul 2>nul
if errorlevel 1 (
    if exist "%ProgramFiles%\Docker\Docker\Docker Desktop.exe" (
        start "" "%ProgramFiles%\Docker\Docker\Docker Desktop.exe"
    ) else if exist "%ProgramFiles(x86)%\Docker\Docker\Docker Desktop.exe" (
        start "" "%ProgramFiles(x86)%\Docker\Docker\Docker Desktop.exe"
    ) else if exist "%LocalAppData%\Programs\Docker\Docker\Docker Desktop.exe" (
        start "" "%LocalAppData%\Programs\Docker\Docker\Docker Desktop.exe"
    )

    set "READY=0"
    for /L %%I in (1,1,30) do (
        docker version >nul 2>nul
        if not errorlevel 1 (
            set "READY=1"
            goto :docker_ready
        )
        timeout /t 2 /nobreak >nul
    )

    :docker_ready
    if "%READY%"=="0" (
        echo Docker Desktop did not become ready in time.
        echo Start Docker Desktop manually, wait until it shows Running, then re-run this script.
        echo You can still play in terminal mode without save/load.
        pause
        exit /b 1
    )
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
echo If the game is currently open, restart it to enable save/load commands.
pause
