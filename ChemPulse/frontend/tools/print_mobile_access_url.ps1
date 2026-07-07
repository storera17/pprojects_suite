param(
    [int]$BackendPort = 8000
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$addresses = Get-NetIPAddress -AddressFamily IPv4 |
    Where-Object {
        $_.IPAddress -notlike "127.*" -and
        $_.IPAddress -notlike "169.254.*" -and
        $_.PrefixOrigin -ne "WellKnown"
    } |
    Sort-Object InterfaceAlias, IPAddress

if (-not $addresses) {
    throw "No LAN IPv4 address found. Connect this PC and iPhone to the same Wi-Fi network."
}

Write-Host "Open one of these URLs in Safari on your iPhone, then Share > Add to Home Screen:"
foreach ($address in $addresses) {
    Write-Host ("  http://{0}:{1}/mobile" -f $address.IPAddress, $BackendPort)
}

Write-Host ""
Write-Host "If the page does not open, run frontend\\tools\\enable_mobile_access.ps1, restart ChemPulse, and allow Windows Firewall access for Python/ChemPulse."