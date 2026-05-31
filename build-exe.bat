@echo off
setlocal
cd /d "%~dp0"

powershell -ExecutionPolicy Bypass -File scripts\build-exe.ps1 -EntryPoint main.py -Name HauntedMansionEscape
if errorlevel 1 (
    echo Build failed.
    exit /b 1
)

echo Build successful. Output: dist\HauntedMansionEscape.exe
