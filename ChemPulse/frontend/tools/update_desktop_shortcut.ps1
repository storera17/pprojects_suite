param(
    [string]$TargetExe = ""
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..\..")

if (!$TargetExe) {
    $Candidates = @(
        (Join-Path $env:LOCALAPPDATA "Programs\ChemPulse\ChemPulse.exe"),
        (Join-Path $Root "dist\ChemPulse\ChemPulse.exe")
    )
    $TargetExe = $Candidates | Where-Object { Test-Path $_ } | Select-Object -First 1
}

if (!$TargetExe -or !(Test-Path $TargetExe)) {
    throw "ChemPulse.exe was not found. Build the desktop app first with frontend\tools\build_windows_app.ps1."
}

$ResolvedTarget = Resolve-Path $TargetExe
$Desktop = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $Desktop "ChemPulse.lnk"
$Shell = New-Object -ComObject WScript.Shell
$Shortcut = $Shell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $ResolvedTarget.Path
$Shortcut.WorkingDirectory = Split-Path -Parent $ResolvedTarget.Path
$Shortcut.IconLocation = $ResolvedTarget.Path
$Shortcut.Description = "Launch the latest local ChemPulse desktop app"
$Shortcut.Save()

Write-Host "Updated desktop shortcut: $ShortcutPath -> $($ResolvedTarget.Path)"
