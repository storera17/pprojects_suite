param(
    [switch]$Disable
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$value = if ($Disable) { "false" } else { "true" }
[Environment]::SetEnvironmentVariable("CHEMPULSE_MOBILE_ACCESS_ENABLED", $value, "User")

if ($Disable) {
    Write-Host "ChemPulse mobile access disabled. Restart ChemPulse for the change to take effect."
} else {
    Write-Host "ChemPulse mobile access enabled. Restart ChemPulse, then run frontend\\tools\\print_mobile_access_url.ps1."
}