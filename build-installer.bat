@echo off
setlocal
cd /d "%~dp0"

powershell -ExecutionPolicy Bypass -File scripts\build-installer.ps1 -Version 1.0.0 -ExeName HauntedMansionEscape.exe
if errorlevel 1 (
    echo Installer build failed.
    exit /b 1
)

echo Installer build successful. Output: installer\dist
