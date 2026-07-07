param(
    [switch]$Clean
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$DistRoot = Join-Path $Root "dist\frontend"
$ZipPath = Join-Path $Root "dist\chempulse-frontend.zip"
Set-Location $Root
$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (!(Test-Path $Python)) {
    $Python = "python"
}

function Copy-CleanDirectory {
    param(
        [Parameter(Mandatory=$true)][string]$Source,
        [Parameter(Mandatory=$true)][string]$Destination
    )

    robocopy $Source $Destination /E /XD __pycache__ .pytest_cache .ruff_cache .mypy_cache /XF *.pyc *.pyo | Out-Null
    if ($LASTEXITCODE -gt 7) {
        throw "robocopy failed for $Source -> $Destination with code $LASTEXITCODE"
    }
    $global:LASTEXITCODE = 0
}

if ($Clean) {
    Remove-Item -LiteralPath $DistRoot, $ZipPath -Recurse -Force -ErrorAction SilentlyContinue
}

Remove-Item -LiteralPath $DistRoot, $ZipPath -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $DistRoot, (Join-Path $Root "dist") | Out-Null

& $Python -m pip install -r requirement\frontend.txt
if ($LASTEXITCODE -ne 0) {
    throw "Frontend dependency install failed with exit code $LASTEXITCODE"
}

Copy-CleanDirectory -Source (Join-Path $Root "frontend") -Destination (Join-Path $DistRoot "frontend")
Copy-CleanDirectory -Source (Join-Path $Root "backend") -Destination (Join-Path $DistRoot "backend")
Copy-Item -LiteralPath (Join-Path $Root "app.py") -Destination $DistRoot -Force
Copy-Item -LiteralPath (Join-Path $Root "backend_app.py") -Destination $DistRoot -Force
Copy-Item -LiteralPath (Join-Path $Root "rxconfig.py") -Destination $DistRoot -Force
Copy-Item -LiteralPath (Join-Path $Root "README.md") -Destination $DistRoot -Force
Copy-Item -LiteralPath (Join-Path $Root "requirement\frontend.txt") -Destination (Join-Path $DistRoot "frontend-requirements.txt") -Force
Copy-Item -LiteralPath (Join-Path $Root "requirement\base.txt") -Destination (Join-Path $DistRoot "base-requirements.txt") -Force

Compress-Archive -Path (Join-Path $DistRoot "*") -DestinationPath $ZipPath -Force
Write-Host "Built frontend bundle at $ZipPath"
