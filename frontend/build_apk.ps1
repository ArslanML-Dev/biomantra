# Build the Bio Mantra debug APK (Windows PowerShell). Run from frontend/:
#   powershell -ExecutionPolicy Bypass -File .\build_apk.ps1
# Needs the Android SDK + JDK 21 from setup_android_sdk.ps1 (Gradle 8.11 cannot run on Java 25/26).
# VITE_API_URL in frontend/.env is the app's default server; the app's Settings page can change it later.
# For a release-style build without cleartext http:  $env:CAP_RELEASE = "1"; .\build_apk.ps1
# Copies the result to ..\BioMantra.apk.
$ErrorActionPreference = "Stop"
$sdk = "$env:LOCALAPPDATA\Android\Sdk"
$jdk = "$env:LOCALAPPDATA\Android\jdk-21"
if (-not (Test-Path $sdk)) { throw "Android SDK not found at $sdk. Run setup_android_sdk.ps1 first." }
if (-not (Test-Path "$jdk\bin\java.exe")) { throw "JDK 21 not found at $jdk. Run setup_android_sdk.ps1 first." }
$env:JAVA_HOME = $jdk
$env:ANDROID_HOME = $sdk
"sdk.dir=$($sdk -replace '\\','/')" | Out-File -Encoding ascii android\local.properties

function Invoke-Step([string]$What, [scriptblock]$Action) {
    # Run a native command and stop with a clear message if it fails.
    & $Action
    if ($LASTEXITCODE -ne 0) { throw "$What failed (exit code $LASTEXITCODE)" }
}

Invoke-Step "npm run build" { npm run build }
Invoke-Step "cap sync" { npx cap sync android }
Push-Location android
try { Invoke-Step "gradle assembleDebug" { .\gradlew.bat assembleDebug } } finally { Pop-Location }
$apk = "android\app\build\outputs\apk\debug\app-debug.apk"
Copy-Item $apk "..\BioMantra.apk" -Force
Write-Host "APK: $((Resolve-Path ..\BioMantra.apk).Path)"
