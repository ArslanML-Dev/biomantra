# Build the Bio Mantra debug APK (Windows PowerShell). Run from frontend/:  .\build_apk.ps1
# Needs: Android Studio opened once so its setup wizard installs the Android SDK.
# Set VITE_API_URL in frontend/.env first (laptop LAN IP for dev, public https URL for the demo).
# For a release-style build without cleartext http:  $env:CAP_RELEASE = "1"; .\build_apk.ps1
$ErrorActionPreference = "Stop"
$env:JAVA_HOME = "C:\Program Files\Android\Android Studio\jbr"
$sdk = "$env:LOCALAPPDATA\Android\Sdk"
if (-not (Test-Path $sdk)) { throw "Android SDK not found at $sdk. Open Android Studio once and finish the setup wizard." }
"sdk.dir=$($sdk -replace '\\','/')" | Out-File -Encoding ascii android\local.properties

npm run build
npx cap sync android
Push-Location android
.\gradlew.bat assembleDebug
Pop-Location
Write-Host "APK: frontend\android\app\build\outputs\apk\debug\app-debug.apk"
