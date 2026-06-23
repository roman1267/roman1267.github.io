Param(
    [string]$ExePath = "dist/HauntedMansionEscape.exe",
    [int]$TimeoutSeconds = 20,
    [switch]$SaveLog
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $ExePath)) {
    throw "Executable not found at '$ExePath'. Build it first with build-exe.bat."
}

$absoluteExePath = (Resolve-Path $ExePath).Path
$artifactDir = Join-Path (Get-Location) "artifacts"
if (-not (Test-Path $artifactDir)) {
    New-Item -ItemType Directory -Path $artifactDir | Out-Null
}
$logPath = Join-Path $artifactDir "exe-smoke.log"

# Scripted CLI flow to validate startup, command processing, and clean shutdown.
$inputText = "help`nquit`n"
$processStartInfo = New-Object System.Diagnostics.ProcessStartInfo
$processStartInfo.FileName = $absoluteExePath
$processStartInfo.RedirectStandardInput = $true
$processStartInfo.RedirectStandardOutput = $true
$processStartInfo.RedirectStandardError = $true
$processStartInfo.UseShellExecute = $false
$processStartInfo.CreateNoWindow = $true
$processStartInfo.WorkingDirectory = (Get-Location).Path

$process = New-Object System.Diagnostics.Process
$process.StartInfo = $processStartInfo

[void]$process.Start()
$process.StandardInput.Write($inputText)
$process.StandardInput.Close()

if (-not $process.WaitForExit($TimeoutSeconds * 1000)) {
    try {
        $process.Kill()
    } catch {
    }
    throw "Smoke test timed out after $TimeoutSeconds seconds."
}

$stdout = $process.StandardOutput.ReadToEnd()
$stderr = $process.StandardError.ReadToEnd()
$combined = $stdout + "`n" + $stderr

if ($SaveLog.IsPresent) {
    Set-Content -Path $logPath -Value $combined -Encoding UTF8
}

$requiredPhrases = @(
    "Welcome to Haunted Mansion Escape",
    "Commands:",
    "Exiting game."
)

$missing = @()
foreach ($phrase in $requiredPhrases) {
    if ($combined -notmatch [Regex]::Escape($phrase)) {
        $missing += $phrase
    }
}

if ($process.ExitCode -ne 0) {
    throw "Executable returned non-zero exit code: $($process.ExitCode)."
}

if ($missing.Count -gt 0) {
    throw "Smoke test failed. Missing expected output fragments: $($missing -join ', ')."
}

Write-Host "Smoke test passed for $ExePath"
Write-Host "Exit code: $($process.ExitCode)"
if ($SaveLog.IsPresent) {
    Write-Host "Log saved: $logPath"
}
