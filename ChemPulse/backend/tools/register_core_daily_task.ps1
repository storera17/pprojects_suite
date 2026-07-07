param(
    [string]$TaskName = "ChemPulse CORE Publication Agent",
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path,
    [string]$Python = "",
    [string]$At = "03:15",
    [string]$StorageDir = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$userCoreApiKey = [Environment]::GetEnvironmentVariable("CORE_API_KEY", "User")
if (-not $env:CORE_API_KEY -and -not $userCoreApiKey) {
    throw "CORE_API_KEY is not set. Store it as a user environment variable before registering the task."
}
if (-not $Python) {
    $venvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
    if (Test-Path $venvPython) {
        $Python = $venvPython
    } else {
        $Python = (Get-Command python).Source
    }
}
$Wrapper = Join-Path $ProjectRoot "backend\tools\run_core_publication_agent.ps1"
if (-not (Test-Path -LiteralPath $Wrapper)) {
    throw "Agent wrapper was not found: $Wrapper"
}
if (-not $StorageDir) {
    $StorageDir = Join-Path $ProjectRoot "backend\storage"
}

$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-ExecutionPolicy Bypass -NoProfile -File `"$Wrapper`" -ProjectRoot `"$ProjectRoot`" -Python `"$Python`" -StorageDir `"$StorageDir`"" `
    -WorkingDirectory $ProjectRoot
$trigger = New-ScheduledTaskTrigger -Daily -At $At
$settings = New-ScheduledTaskSettingsSet `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Hours 2) `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -WakeToRun

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Description "Downloads filtered CORE journal publication metadata into ChemPulse once per day." `
    -Force | Out-Null

Write-Host "Registered scheduled task '$TaskName' for daily execution at $At."
Write-Host "Daily collection updates should be reviewed through the Codex automation named 'ChemPulse Daily Collection Update'."
