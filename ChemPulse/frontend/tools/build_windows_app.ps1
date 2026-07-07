param(
    [switch]$Clean
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $Root
$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (!(Test-Path $Python)) {
    $Python = "python"
}

if ($Clean) {
    Remove-Item -LiteralPath "build", "dist" -Recurse -Force -ErrorAction SilentlyContinue
}

Remove-Item -LiteralPath (Join-Path $Root "dist\ChemPulse"), (Join-Path $Root "build\ChemPulse") -Recurse -Force -ErrorAction SilentlyContinue

& $Python -m pip install -r requirement\frontend.txt pyinstaller
if ($LASTEXITCODE -ne 0) {
    throw "pip install failed with exit code $LASTEXITCODE"
}

& $Python -m PyInstaller `
    --clean `
    --noconfirm `
    --windowed `
    --name ChemPulse `
    --add-data "rxconfig.py;." `
    --add-data "frontend;frontend" `
    --add-data "backend;backend" `
    --add-data "app.py;." `
    --add-data "backend_app.py;." `
    desktop_app.py
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller failed with exit code $LASTEXITCODE"
}

$ShortcutScript = Join-Path $PSScriptRoot "update_desktop_shortcut.ps1"
if (Test-Path $ShortcutScript) {
    powershell -ExecutionPolicy Bypass -NoProfile -File $ShortcutScript -TargetExe (Join-Path $Root "dist\ChemPulse\ChemPulse.exe")
}

Write-Host "Built desktop launcher at $Root\dist\ChemPulse\ChemPulse.exe"
