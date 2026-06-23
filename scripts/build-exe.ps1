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
& .venv/Scripts/python.exe -m pip install pyinstaller==6.21.0

& .venv/Scripts/pyinstaller.exe `
    --clean `
    --noconfirm `
    --onefile `
    --name $Name `
    --collect-submodules pymongo `
    --collect-submodules bson `
    $EntryPoint

if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller build failed with exit code $LASTEXITCODE."
}

Write-Host "Build complete: dist/$Name.exe"
