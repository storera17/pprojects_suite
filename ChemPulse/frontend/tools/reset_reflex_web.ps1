Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $Root
$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (!(Test-Path $Python)) {
    $Python = "python"
}

$lockedProcesses = @(
    Get-CimInstance Win32_Process |
        Where-Object {
            $_.Name -match "python|node|bun|react-router|reflex" -and
            $_.CommandLine -match ([regex]::Escape($Root.Path) + "|reflex|react-router")
        }
)

foreach ($process in $lockedProcesses) {
    Stop-Process -Id $process.ProcessId -Force -ErrorAction SilentlyContinue
}

Start-Sleep -Seconds 2
Remove-Item -LiteralPath ".web" -Recurse -Force -ErrorAction SilentlyContinue
& $Python -m reflex init
