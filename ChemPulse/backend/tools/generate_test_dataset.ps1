param(
    [int]$Rows = 1000000,
    [int]$Scaffolds = 5000,
    [int]$Clusters = 240,
    [int]$Publications = 120000,
    [string]$OutputPath = ""
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $Root
$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (!(Test-Path $Python)) {
    $Python = "python"
}

$args = @(
    "-m", "backend.data.synthetic_dataset",
    "--rows", $Rows,
    "--scaffolds", $Scaffolds,
    "--clusters", $Clusters,
    "--publications", $Publications
)

if ($OutputPath) {
    $args += @("--output", $OutputPath)
}

& $Python @args
