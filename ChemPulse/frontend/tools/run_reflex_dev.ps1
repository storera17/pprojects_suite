param(
    [int]$FrontendPort = 3002,
    [int]$BackendPort = 8010,
    [switch]$ResetWeb
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $Root
$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (!(Test-Path $Python)) {
    $Python = "python"
}

$env:FRONTEND_PORT = [string]$FrontendPort
$env:BACKEND_PORT = [string]$BackendPort
$env:CHEMPULSE_API_BASE_URL = "http://127.0.0.1:$BackendPort"
$env:CHEMPULSE_DEPLOY_URL = "http://127.0.0.1:$FrontendPort"
$env:CHEMPULSE_STORAGE_DIR = Join-Path $Root "backend\storage"

$envPayload = @{
    PING = "http://127.0.0.1:$BackendPort"
    EVENT = "ws://127.0.0.1:$BackendPort/_event"
    CHEMPULSE_API_BASE_URL = "http://127.0.0.1:$BackendPort"
    CHEMPULSE_DEPLOY_URL = "http://127.0.0.1:$FrontendPort"
} | ConvertTo-Json -Depth 4

foreach ($dir in @((Join-Path $Root ".web\\public"))) {
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
    Set-Content -Path (Join-Path $dir "env.json") -Value $envPayload -Encoding UTF8
}

if ($ResetWeb) {
    powershell -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "reset_reflex_web.ps1")
}

& $Python -m reflex run --frontend-port $FrontendPort --backend-port $BackendPort

