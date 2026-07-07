Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$secureKey = Read-Host "Paste your CORE API key" -AsSecureString
$plainKey = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
    [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureKey)
)

if ([string]::IsNullOrWhiteSpace($plainKey)) {
    throw "No CORE API key was provided."
}

[Environment]::SetEnvironmentVariable("CORE_API_KEY", $plainKey.Trim(), "User")
Write-Host "CORE_API_KEY saved to your Windows user environment. Open a new PowerShell window before running the agent."
