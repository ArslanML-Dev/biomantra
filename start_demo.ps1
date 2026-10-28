# Bio Mantra demo launcher: starts the backend (port 8000) and the website (port 5173) on this laptop
# so a phone on the same Wi-Fi can use them.
#
# Run (from this folder):        powershell -ExecutionPolicy Bypass -File .\start_demo.ps1
# Clean demo (empty database):   powershell -ExecutionPolicy Bypass -File .\start_demo.ps1 -Fresh
# One-time firewall rules, ONLY ports 8000 + 5173, Private Wi-Fi only (run in an Administrator PowerShell):
#                                powershell -ExecutionPolicy Bypass -File .\start_demo.ps1 -Firewall
param([switch]$Fresh, [switch]$Firewall)
$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
$Backend = Join-Path $Root "backend"
$Frontend = Join-Path $Root "frontend"
$Python = Join-Path $Backend ".venv\Scripts\python.exe"
$Ports = @(8000, 5173)

function Write-Big([string]$Text, [string]$Color = "Green") {
    # Print one line inside a wide coloured box so it is easy to read from a distance.
    $line = "=" * 70
    Write-Host ""
    Write-Host $line -ForegroundColor $Color
    Write-Host ("   " + $Text) -ForegroundColor $Color
    Write-Host $line -ForegroundColor $Color
}

function Get-WifiIp {
    # The laptop's IPv4 address on the network that has internet (the Wi-Fi the phone must join).
    $cfg = Get-NetIPConfiguration | Where-Object { $_.IPv4DefaultGateway -and $_.NetAdapter.Status -eq "Up" } |
        Sort-Object { $_.InterfaceAlias -notlike "Wi-Fi*" } | Select-Object -First 1
    if (-not $cfg) { throw "No connected Wi-Fi/network found. Connect the laptop to Wi-Fi and try again." }
    return $cfg.IPv4Address.IPAddress
}

function Test-Admin {
    # True if this PowerShell window was started with "Run as administrator".
    $id = [Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
    return $id.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Wait-Url([string]$Url, [int]$Seconds = 90) {
    # Poll a URL until it answers, or give up after $Seconds.
    for ($i = 0; $i -lt $Seconds; $i++) {
        try { Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 3 | Out-Null; return $true } catch { Start-Sleep 1 }
    }
    return $false
}

# ---------- one-time firewall rules (only ports 8000 and 5173, Private networks only) ----------
if ($Firewall) {
    if (-not (Test-Admin)) { throw "Open PowerShell with 'Run as administrator' to add the firewall rules." }
    foreach ($port in $Ports) {
        $name = "Bio Mantra demo TCP $port"
        Get-NetFirewallRule -DisplayName $name -ErrorAction SilentlyContinue | Remove-NetFirewallRule
        New-NetFirewallRule -DisplayName $name -Direction Inbound -Protocol TCP -LocalPort $port `
            -Action Allow -Profile Private | Out-Null
        Write-Host "Added firewall rule: $name (Private networks only)" -ForegroundColor Green
    }
    Write-Host "Done. Now run the script again WITHOUT -Firewall, in a normal PowerShell window."
    exit 0
}

# ---------- checks ----------
if (-not (Test-Path $Python)) { throw "Backend venv missing: $Python. See README.md 'Backend' setup." }
if (-not (Test-Path (Join-Path $Frontend "node_modules"))) {
    Write-Host "Installing website packages (first time only)..."
    Push-Location $Frontend; npm install; Pop-Location
}
$ip = Get-WifiIp
$netProfile = (Get-NetConnectionProfile | Where-Object { $_.IPv4Connectivity -eq "Internet" } | Select-Object -First 1).NetworkCategory
$rulesOk = @($Ports | Where-Object { Get-NetFirewallRule -DisplayName "Bio Mantra demo TCP $_" -ErrorAction SilentlyContinue }).Count -eq $Ports.Count

if ($Fresh) {
    Remove-Item (Join-Path $Backend "biomantra.db") -ErrorAction SilentlyContinue
    Remove-Item (Join-Path $Backend "uploads\*.jpg") -ErrorAction SilentlyContinue
    Write-Host "Fresh start: database and uploaded photos cleared." -ForegroundColor Yellow
}

# ---------- start both servers in their own windows ----------
Write-Host "Starting backend (port 8000) and website (port 5173)..."
$backendProc = Start-Process -FilePath $Python -WorkingDirectory $Backend -PassThru `
    -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"
$webProc = Start-Process -FilePath "cmd.exe" -WorkingDirectory $Frontend -PassThru `
    -ArgumentList "/c", "npm run dev -- --host 0.0.0.0 --port 5173 --strictPort"

$backendUp = Wait-Url "http://localhost:8000/health"
$webUp = Wait-Url "http://localhost:5173/"
if (-not $backendUp) { Write-Host "Backend did not start. Look at its window for the error." -ForegroundColor Red }
if (-not $webUp) { Write-Host "Website did not start. Look at its window for the error." -ForegroundColor Red }

# ---------- the two addresses, in big text ----------
Write-Big "LAPTOP BROWSER - open this website:   http://localhost:5173" "Cyan"
Write-Big "PHONE BROWSER  - open this website:   http://${ip}:5173" "Cyan"
Write-Big "PHONE APP - Settings > Server URL:    http://${ip}:8000" "Green"
Write-Host ""
Write-Host "Admin page: http://localhost:5173/admin   (token = ADMIN_TOKEN in backend\.env)"
Write-Host "The phone must be on the SAME Wi-Fi as this laptop."

# ---------- firewall help ----------
if ($netProfile -ne "Private") {
    Write-Host ""
    Write-Host "WARNING: this Wi-Fi is set to '$netProfile'. The phone may not connect." -ForegroundColor Yellow
    Write-Host "Fix: Windows Settings > Network & internet > Wi-Fi > (your network) > Network profile type: Private" -ForegroundColor Yellow
}
Write-Host ""
Write-Host "IF A 'Windows Security Alert' (firewall) WINDOW APPEARS for python.exe or node.exe:" -ForegroundColor Yellow
Write-Host "   1. Tick  [x] Private networks" -ForegroundColor Yellow
Write-Host "   2. UNtick [ ] Public networks" -ForegroundColor Yellow
Write-Host "   3. Click 'Allow access'   (do NOT click Cancel - that blocks the phone)" -ForegroundColor Yellow
if (-not $rulesOk) {
    Write-Host "Tighter option (only ports 8000 + 5173): open PowerShell as Administrator in this folder and run once:" -ForegroundColor Yellow
    Write-Host "   powershell -ExecutionPolicy Bypass -File .\start_demo.ps1 -Firewall" -ForegroundColor Yellow
}

# ---------- stop ----------
Write-Host ""
Read-Host "Demo is running. Press Enter here to STOP both servers"
foreach ($p in @($backendProc, $webProc)) { & taskkill.exe /T /F /PID $p.Id 2>$null | Out-Null }
Write-Host "Stopped."
