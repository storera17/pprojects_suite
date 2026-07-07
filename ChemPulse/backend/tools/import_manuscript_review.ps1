param(
    [Parameter(Mandatory=$true)]
    [string]$Path,

    [string]$SourceLabel = ""
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $Root

$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (!(Test-Path $Python)) {
    $Python = "python"
}

$ArgsList = @("-m", "backend.data.manuscript_review_importer", $Path)
if ($SourceLabel) {
    $ArgsList += @("--source-label", $SourceLabel)
}

& $Python @ArgsList