param(    
    [Parameter(Mandatory=$true)]
    [string]$Path,

    [switch]$NoRecursive
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $Root

$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (!(Test-Path $Python)) {
    $Python = "python"
}

$ArgsList = @("-m", "backend.data.manual_publication_importer", $Path)
if ($NoRecursive) {
    $ArgsList += "--no-recursive"
}

& $Python @ArgsList