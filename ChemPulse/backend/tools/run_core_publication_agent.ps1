param(
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path,
    [string]$Python = "",
    [string]$StorageDir = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$logDir = Join-Path $ProjectRoot "backend\storage\logs"
New-Item -ItemType Directory -Path $logDir -Force | Out-Null

if (-not $Python) {
    $venvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
    if (Test-Path -LiteralPath $venvPython) {
        $Python = $venvPython
    } else {
        $Python = (Get-Command python).Source
    }
}

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$stdoutLog = Join-Path $logDir "core-publication-agent-$timestamp.log"
$stderrLog = Join-Path $logDir "core-publication-agent-$timestamp.err.log"
$wrapperLog = Join-Path $logDir "core-publication-agent-$timestamp.wrapper.log"

$userCoreApiKey = [Environment]::GetEnvironmentVariable("CORE_API_KEY", "User")
if (-not $env:CORE_API_KEY -and $userCoreApiKey) {
    $env:CORE_API_KEY = $userCoreApiKey
}
foreach ($name in @(
    "CHEMPULSE_SCAFFOLD_LIST_PATH",
    "CHEMPULSE_REPORT_EMAIL_TO",
    "CHEMPULSE_REPORT_EMAIL_FROM",
    "CHEMPULSE_SMTP_HOST",
    "CHEMPULSE_SMTP_PORT",
    "CHEMPULSE_SMTP_USERNAME",
    "CHEMPULSE_SMTP_PASSWORD",
    "CHEMPULSE_SMTP_USE_TLS",
    "CHEMPULSE_EMAIL_REPORTS_ENABLED"
)) {
    $userValue = [Environment]::GetEnvironmentVariable($name, "User")
    if (-not [Environment]::GetEnvironmentVariable($name, "Process") -and $userValue) {
        [Environment]::SetEnvironmentVariable($name, $userValue, "Process")
    }
}
if ($StorageDir) {
    $env:CHEMPULSE_STORAGE_DIR = $StorageDir
} elseif (-not $env:CHEMPULSE_STORAGE_DIR) {
    $env:CHEMPULSE_STORAGE_DIR = Join-Path $ProjectRoot "backend\storage"
}
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUNBUFFERED = "1"
$env:CHEMPULSE_REPORT_DIR = Join-Path $env:CHEMPULSE_STORAGE_DIR "reports"
if (-not $env:CHEMPULSE_CORE_MIN_INSERTED_SUCCESS) {
    $env:CHEMPULSE_CORE_MIN_INSERTED_SUCCESS = "15"
}
New-Item -ItemType Directory -Path $env:CHEMPULSE_STORAGE_DIR, $env:CHEMPULSE_REPORT_DIR -Force | Out-Null

Push-Location $ProjectRoot
try {
    "ProjectRoot=$ProjectRoot" | Out-File -LiteralPath $wrapperLog -Encoding UTF8
    "Python=$Python" | Out-File -LiteralPath $wrapperLog -Encoding UTF8 -Append
    "PythonExists=$(Test-Path -LiteralPath $Python)" | Out-File -LiteralPath $wrapperLog -Encoding UTF8 -Append
    "StorageDir=$env:CHEMPULSE_STORAGE_DIR" | Out-File -LiteralPath $wrapperLog -Encoding UTF8 -Append
    "CoreApiKeyPresent=$([bool]$env:CORE_API_KEY)" | Out-File -LiteralPath $wrapperLog -Encoding UTF8 -Append
    "EmailReportRecipientPresent=$([bool]$env:CHEMPULSE_REPORT_EMAIL_TO)" | Out-File -LiteralPath $wrapperLog -Encoding UTF8 -Append
    "EmailReportSmtpPresent=$([bool]$env:CHEMPULSE_SMTP_HOST)" | Out-File -LiteralPath $wrapperLog -Encoding UTF8 -Append
    "MinInsertedSuccess=$env:CHEMPULSE_CORE_MIN_INSERTED_SUCCESS" | Out-File -LiteralPath $wrapperLog -Encoding UTF8 -Append

    if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) {
        throw "Python runtime was not found: $Python"
    }

    $restoreNativeCommandPreference = $false
    $previousNativeCommandPreference = $null
    if (Test-Path variable:PSNativeCommandUseErrorActionPreference) {
        $restoreNativeCommandPreference = $true
        $previousNativeCommandPreference = $PSNativeCommandUseErrorActionPreference
        $PSNativeCommandUseErrorActionPreference = $false
    }
    try {
        & $Python -m backend.agents.core_publication_agent 1> $stdoutLog 2> $stderrLog
        $pythonExitCode = $LASTEXITCODE
    } finally {
        if ($restoreNativeCommandPreference) {
            $PSNativeCommandUseErrorActionPreference = $previousNativeCommandPreference
        }
    }

    "PythonExitCode=$pythonExitCode" | Out-File -LiteralPath $wrapperLog -Encoding UTF8 -Append
    if ($pythonExitCode -ne 0) {
        $stderrTail = Get-Content -LiteralPath $stderrLog -Tail 40 -ErrorAction SilentlyContinue
        if ($stderrTail) {
            "PythonStderrTail:" | Out-File -LiteralPath $wrapperLog -Encoding UTF8 -Append
            $stderrTail | Out-File -LiteralPath $wrapperLog -Encoding UTF8 -Append
        }
        throw "CORE publication agent exited with code $pythonExitCode. See $stderrLog"
    }
    Get-Content $stdoutLog
} catch {
    "WrapperError=$($_.Exception.Message)" | Out-File -LiteralPath $wrapperLog -Encoding UTF8 -Append
    throw
}
finally {
    Pop-Location
}
