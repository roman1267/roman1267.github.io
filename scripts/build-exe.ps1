Param(
    [string]$EntryPoint = "main.py",
    [string]$Name = "HauntedMansionEscape"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path ".venv/Scripts/python.exe")) {
    py -m venv .venv
}

& .venv/Scripts/python.exe -m pip install --upgrade pip
& .venv/Scripts/python.exe -m pip install -r requirements.txt
& .venv/Scripts/python.exe -m pip install pyinstaller==6.10.0

& .venv/Scripts/pyinstaller.exe --clean --noconfirm --onefile --name $Name $EntryPoint

Write-Host "Build complete: dist/$Name.exe"
