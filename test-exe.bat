@echo off
setlocal
cd /d "%~dp0"

powershell -ExecutionPolicy Bypass -File scripts\test-exe-smoke.ps1 -ExePath dist\HauntedMansionEscape.exe -SaveLog
if errorlevel 1 (
    echo Executable smoke test failed.
    exit /b 1
)

echo Executable smoke test passed.
