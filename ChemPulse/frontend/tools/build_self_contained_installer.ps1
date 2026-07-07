param(
    [switch]$Clean
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$BuildRoot = Join-Path $Root "build\installer"
$PackageRoot = Join-Path $BuildRoot "package\ChemPulse"
$CacheRoot = Join-Path $BuildRoot "cache"
$WorkRoot = Join-Path $BuildRoot "iexpress"
$PayloadTar = Join-Path $WorkRoot "payload.tar"
$InstallerExe = Join-Path $Root "dist\ChemPulseSetup.exe"
$DesktopDistRoot = Join-Path $Root "dist\ChemPulse"
$PyInstallerBuildRoot = Join-Path $Root "build\ChemPulse"
$PythonVersion = "3.13.13"
$PythonEmbedUrl = "https://www.python.org/ftp/python/$PythonVersion/python-$PythonVersion-embed-amd64.zip"
$PythonEmbedZip = Join-Path $CacheRoot "python-$PythonVersion-embed-amd64.zip"
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
    Remove-Item -LiteralPath $BuildRoot, $InstallerExe -Recurse -Force -ErrorAction SilentlyContinue
}

Remove-Item -LiteralPath $PackageRoot, $DesktopDistRoot, $PyInstallerBuildRoot -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $BuildRoot, $PackageRoot, $CacheRoot, $WorkRoot, (Join-Path $Root "dist") | Out-Null

& $Python -m pip install -r requirement\frontend.txt pyinstaller -q
& $Python -m PyInstaller --clean --noconfirm --windowed --name ChemPulse desktop_app.py

Copy-CleanDirectory -Source (Join-Path $Root "dist\ChemPulse") -Destination $PackageRoot
Copy-CleanDirectory -Source (Join-Path $Root "frontend") -Destination (Join-Path $PackageRoot "frontend")
Copy-CleanDirectory -Source (Join-Path $Root "backend") -Destination (Join-Path $PackageRoot "backend")
Copy-CleanDirectory -Source (Join-Path $Root ".web") -Destination (Join-Path $PackageRoot ".web")

Copy-Item -LiteralPath (Join-Path $Root "rxconfig.py") -Destination $PackageRoot -Force
Copy-Item -LiteralPath (Join-Path $Root "README.md") -Destination $PackageRoot -Force
Copy-Item -LiteralPath (Join-Path $Root "app.py") -Destination $PackageRoot -Force
Copy-Item -LiteralPath (Join-Path $Root "backend_app.py") -Destination $PackageRoot -Force
Copy-Item -LiteralPath (Join-Path $Root "desktop_app.py") -Destination $PackageRoot -Force

$StorageDest = Join-Path $PackageRoot "backend\storage"
New-Item -ItemType Directory -Force -Path $StorageDest | Out-Null
if (Test-Path (Join-Path $Root "backend\storage\chempulse.duckdb")) {
    Copy-Item -LiteralPath (Join-Path $Root "backend\storage\chempulse.duckdb") -Destination $StorageDest -Force
}

if (!(Test-Path $PythonEmbedZip)) {
    Invoke-WebRequest -Uri $PythonEmbedUrl -OutFile $PythonEmbedZip
}

$RuntimeRoot = Join-Path $PackageRoot "runtime"
$RuntimeSitePackages = Join-Path $RuntimeRoot "Lib\site-packages"
New-Item -ItemType Directory -Force -Path $RuntimeRoot, $RuntimeSitePackages | Out-Null
Expand-Archive -LiteralPath $PythonEmbedZip -DestinationPath $RuntimeRoot -Force

$PthFile = Get-ChildItem -LiteralPath $RuntimeRoot -Filter "python*._pth" | Select-Object -First 1
if ($PthFile) {
    $pth = Get-Content -LiteralPath $PthFile.FullName
    if ($pth -notcontains "..") {
        $pth = @($pth) + ".."
    }
    if ($pth -notcontains "Lib\site-packages") {
        $pth = @($pth) + "Lib\site-packages"
    }
    $pth = $pth | ForEach-Object { if ($_ -eq "#import site") { "import site" } else { $_ } }
    Set-Content -LiteralPath $PthFile.FullName -Value $pth -Encoding ASCII
}

& $Python -m pip install `
    --target $RuntimeSitePackages `
    -r (Join-Path $Root "requirement\\frontend.txt") `
    -q

$BunSource = Join-Path $env:LOCALAPPDATA "reflex\bun"
if (!(Test-Path $BunSource)) {
    & $Python -m reflex init --loglevel error | Out-Null
}
Copy-CleanDirectory -Source $BunSource -Destination (Join-Path $RuntimeRoot "bun")

$BundledNodeCandidates = @(
    (Join-Path $env:LOCALAPPDATA "OpenAI\Codex\bin\node.exe"),
    (Join-Path $env:LOCALAPPDATA "OpenAI\Codex\bin\5b9024f90663758b\node.exe"),
    "C:\Program Files\nodejs\node.exe"
)
$BundledNode = $BundledNodeCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if ($BundledNode) {
    $NodeDest = Join-Path $RuntimeRoot "node"
    New-Item -ItemType Directory -Force -Path $NodeDest | Out-Null
    Copy-Item -LiteralPath $BundledNode -Destination (Join-Path $NodeDest "node.exe") -Force
}

$UninstallScript = @'
$ErrorActionPreference = "SilentlyContinue"
$InstallDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Programs = [Environment]::GetFolderPath("Programs")
$Desktop = [Environment]::GetFolderPath("Desktop")
Remove-Item -LiteralPath (Join-Path $Programs "ChemPulse.lnk") -Force
Remove-Item -LiteralPath (Join-Path $Desktop "ChemPulse.lnk") -Force
Remove-Item -LiteralPath "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\ChemPulse" -Recurse -Force
Start-Sleep -Milliseconds 300
Remove-Item -LiteralPath $InstallDir -Recurse -Force
'@
Set-Content -LiteralPath (Join-Path $PackageRoot "uninstall.ps1") -Value $UninstallScript -Encoding UTF8

Remove-Item -LiteralPath $PayloadTar -Force -ErrorAction SilentlyContinue
Push-Location (Join-Path $BuildRoot "package")
try {
    tar -cf $PayloadTar ChemPulse
} finally {
    Pop-Location
}

$InstallPs1 = @'
$ErrorActionPreference = "Stop"
$InstallDir = Join-Path $env:LOCALAPPDATA "Programs\ChemPulse"
$Payload = Join-Path $PSScriptRoot "payload.tar"
if (Test-Path $InstallDir) {
    Remove-Item -LiteralPath $InstallDir -Recurse -Force
}
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $InstallDir) | Out-Null
tar -xf $Payload -C (Split-Path -Parent $InstallDir)

$Exe = Join-Path $InstallDir "ChemPulse.exe"
$Shell = New-Object -ComObject WScript.Shell
$Programs = [Environment]::GetFolderPath("Programs")
$Desktop = [Environment]::GetFolderPath("Desktop")
foreach ($ShortcutPath in @((Join-Path $Programs "ChemPulse.lnk"), (Join-Path $Desktop "ChemPulse.lnk"))) {
    $Shortcut = $Shell.CreateShortcut($ShortcutPath)
    $Shortcut.TargetPath = $Exe
    $Shortcut.WorkingDirectory = $InstallDir
    $Shortcut.IconLocation = $Exe
    $Shortcut.Save()
}

$UninstallKey = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\ChemPulse"
New-Item -Path $UninstallKey -Force | Out-Null
Set-ItemProperty -Path $UninstallKey -Name DisplayName -Value "ChemPulse"
Set-ItemProperty -Path $UninstallKey -Name DisplayVersion -Value "0.1.0"
Set-ItemProperty -Path $UninstallKey -Name Publisher -Value "ChemPulse"
Set-ItemProperty -Path $UninstallKey -Name InstallLocation -Value $InstallDir
Set-ItemProperty -Path $UninstallKey -Name DisplayIcon -Value $Exe
Set-ItemProperty -Path $UninstallKey -Name UninstallString -Value "powershell.exe -ExecutionPolicy Bypass -NoProfile -File `"$InstallDir\uninstall.ps1`""

Start-Process -FilePath $Exe -WorkingDirectory $InstallDir
'@
Set-Content -LiteralPath (Join-Path $WorkRoot "install.ps1") -Value $InstallPs1 -Encoding UTF8

$InstallCmd = '@echo off
powershell.exe -ExecutionPolicy Bypass -NoProfile -File "%~dp0install.ps1"
'
Set-Content -LiteralPath (Join-Path $WorkRoot "install.cmd") -Value $InstallCmd -Encoding ASCII

$SedPath = Join-Path $WorkRoot "ChemPulseSetup.sed"
$Sed = @"
[Version]
Class=IEXPRESS
SEDVersion=3
[Options]
PackagePurpose=InstallApp
ShowInstallProgramWindow=0
HideExtractAnimation=1
UseLongFileName=1
InsideCompressed=0
CAB_FixedSize=0
CAB_ResvCodeSigning=0
RebootMode=N
InstallPrompt=
DisplayLicense=
FinishMessage=ChemPulse has been installed.
TargetName=$InstallerExe
FriendlyName=ChemPulse Installer
AppLaunched=install.cmd
PostInstallCmd=<None>
AdminQuietInstCmd=install.cmd
UserQuietInstCmd=install.cmd
SourceFiles=SourceFiles
[SourceFiles]
SourceFiles0=$WorkRoot\
[SourceFiles0]
%FILE0%=
%FILE1%=
%FILE2%=
[Strings]
FILE0="install.cmd"
FILE1="install.ps1"
FILE2="payload.tar"
"@
Set-Content -LiteralPath $SedPath -Value $Sed -Encoding ASCII

iexpress.exe /N /Q $SedPath
Write-Host "Built self-contained installer at $InstallerExe"


