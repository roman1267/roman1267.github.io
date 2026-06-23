Param(
    [string]$Version = "1.0.0",
    [string]$ExeName = "HauntedMansionEscape.exe",
    [string]$InnoCompilerPath = ""
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path "dist/$ExeName")) {
    throw "dist/$ExeName not found. Build the executable first with build-exe.bat."
}

$scriptPath = "installer/HauntedMansionEscape.iss"
if (-not (Test-Path $scriptPath)) {
    throw "Installer script not found: $scriptPath"
}

$compilerCandidates = @()
if ($InnoCompilerPath) {
    $compilerCandidates += $InnoCompilerPath
}
$compilerCandidates += @(
    "iscc.exe",
    "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles(x86)\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
)

$compiler = $null
foreach ($candidate in $compilerCandidates) {
    if ($candidate -eq "iscc.exe") {
        $cmd = Get-Command iscc.exe -ErrorAction SilentlyContinue
        if ($cmd) {
            $compiler = $cmd.Source
            break
        }
    } elseif (Test-Path $candidate) {
        $compiler = $candidate
        break
    }
}

if (-not $compiler) {
    throw "Inno Setup compiler (ISCC.exe) not found. Install Inno Setup 6 or pass -InnoCompilerPath."
}

$outDir = "installer/dist"
if (-not (Test-Path $outDir)) {
    New-Item -ItemType Directory -Path $outDir | Out-Null
}

& $compiler "/DMyAppVersion=$Version" "/DMyExeName=$ExeName" $scriptPath
if ($LASTEXITCODE -ne 0) {
    throw "Inno Setup compilation failed with exit code $LASTEXITCODE."
}

Write-Host "Installer build complete. Output folder: installer/dist"
