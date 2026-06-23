@echo off
setlocal
cd /d "%~dp0"

set "LOGFILE=%TEMP%\haunted-mongo-setup.log"
echo =============================================================== > "%LOGFILE%"
echo [%date% %time%] Start-Save-DB launched >> "%LOGFILE%"

echo Starting MongoDB for save/load support using Docker...
echo Logging to: %LOGFILE%

net session >nul 2>nul
if errorlevel 1 (
    echo Requesting administrator privileges...
    echo [%date% %time%] Elevation requested >> "%LOGFILE%"
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b 0
)

where docker >nul 2>nul
if errorlevel 1 (
    echo Docker CLI not found. Attempting Docker Desktop install via winget...
    echo [%date% %time%] Docker CLI missing. Trying winget install. >> "%LOGFILE%"
    where winget >nul 2>nul
    if not errorlevel 1 (
        winget install --id Docker.DockerDesktop -e --accept-source-agreements --accept-package-agreements >> "%LOGFILE%" 2>&1
    )

    where docker >nul 2>nul
    if errorlevel 1 (
        echo winget path failed or is unavailable. Trying direct Docker installer download...
        echo [%date% %time%] Falling back to direct installer download. >> "%LOGFILE%"
        set "DOCKER_INSTALLER=%TEMP%\DockerDesktopInstaller.exe"
        powershell -NoProfile -ExecutionPolicy Bypass -Command "Invoke-WebRequest -Uri 'https://desktop.docker.com/win/main/amd64/Docker%%20Desktop%%20Installer.exe' -OutFile '%DOCKER_INSTALLER%'" >> "%LOGFILE%" 2>&1
        if errorlevel 1 (
            echo Could not download Docker Desktop installer.
            echo Install manually from https://www.docker.com/products/docker-desktop/
            echo [%date% %time%] Direct installer download failed. >> "%LOGFILE%"
            pause
            exit /b 1
        )

        "%DOCKER_INSTALLER%" install --quiet --accept-license >> "%LOGFILE%" 2>&1
        if errorlevel 1 (
            echo Automatic Docker installation failed.
            echo Install Docker Desktop manually, then run this script again.
            echo [%date% %time%] Docker installer execution failed. >> "%LOGFILE%"
            pause
            exit /b 1
        )
    )
)

if exist "%ProgramFiles%\Docker\Docker\resources\bin\docker.exe" (
    set "PATH=%ProgramFiles%\Docker\Docker\resources\bin;%PATH%"
)
if exist "%ProgramFiles(x86)%\Docker\Docker\resources\bin\docker.exe" (
    set "PATH=%ProgramFiles(x86)%\Docker\Docker\resources\bin;%PATH%"
)
if exist "%LocalAppData%\Programs\Docker\Docker\resources\bin\docker.exe" (
    set "PATH=%LocalAppData%\Programs\Docker\Docker\resources\bin;%PATH%"
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
    for /L %%I in (1,1,60) do (
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
        echo Setup log: %LOGFILE%
        echo [%date% %time%] Docker daemon not ready after wait loop. >> "%LOGFILE%"
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
        echo [%date% %time%] Existing container start failed. >> "%LOGFILE%"
        pause
        exit /b 1
    )
)

echo MongoDB container "%CONTAINER_NAME%" is running on localhost:27017.
echo Save/load is now available in game.
echo If the game is currently open, restart it to enable save/load commands.
echo [%date% %time%] Success. MongoDB container running. >> "%LOGFILE%"
pause
