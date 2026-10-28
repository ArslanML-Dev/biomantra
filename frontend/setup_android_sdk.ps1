# Install the Android SDK without the Android Studio UI (Windows PowerShell). Run from frontend/:
#   powershell -ExecutionPolicy Bypass -File .\setup_android_sdk.ps1
# Downloads Google's official command-line tools (SHA-1 checked), sets ANDROID_HOME / ANDROID_SDK_ROOT
# for the current user, accepts the SDK licences (running this script means you accept them) and installs
# what the Capacitor 7 project needs: platform-tools, platforms;android-35, build-tools;34.0.0 (AGP 8.7 default).
# It also unpacks a portable JDK 21 (Microsoft Build of OpenJDK, SHA-256 checked) into the user's
# AppData, because Gradle 8.11 (Capacitor 7) cannot run on Android Studio's Java 25.
# Every download is retried up to 3 times for slow/unstable internet.
$ErrorActionPreference = "Stop"
$Sdk = "$env:LOCALAPPDATA\Android\Sdk"
$Jdk = "$env:LOCALAPPDATA\Android\jdk-21"
$JdkUrl = "https://aka.ms/download-jdk/microsoft-jdk-21-windows-x64.zip"
$ToolsZip = "commandlinetools-win-13114758_latest.zip"
$ToolsSha1 = "54a582f3bf73e04253602f2d1c80bd5868aac115"   # from dl.google.com/android/repository/repository2-3.xml
$Packages = @("platform-tools", "platforms;android-35", "build-tools;34.0.0")
$env:JAVA_HOME = "C:\Program Files\Android\Android Studio\jbr"

function Invoke-WithRetry([scriptblock]$Action, [string]$What) {
    # Run $Action up to 3 times, waiting longer after each failure.
    for ($try = 1; $try -le 3; $try++) {
        try { & $Action; if ($LASTEXITCODE -and $LASTEXITCODE -ne 0) { throw "exit code $LASTEXITCODE" }; return }
        catch { Write-Host "$What failed (attempt $try/3): $_" -ForegroundColor Yellow; if ($try -eq 3) { throw }; Start-Sleep (15 * $try) }
    }
}

# 1. command-line tools -> $Sdk\cmdline-tools\latest
$sdkmanager = "$Sdk\cmdline-tools\latest\bin\sdkmanager.bat"
if (-not (Test-Path $sdkmanager)) {
    $tmp = Join-Path $env:TEMP "android-cmdline-tools"
    New-Item -ItemType Directory -Force $tmp | Out-Null
    $zip = Join-Path $tmp $ToolsZip
    Invoke-WithRetry {
        & curl.exe -fL --retry 3 --retry-delay 10 -C - -o $zip "https://dl.google.com/android/repository/$ToolsZip"
        $hash = (Get-FileHash $zip -Algorithm SHA1).Hash.ToLower()
        if ($hash -ne $ToolsSha1) { Remove-Item $zip; throw "SHA-1 mismatch ($hash)" }
    } "Download of $ToolsZip"
    $unpack = Join-Path $tmp "unpacked"
    Remove-Item $unpack -Recurse -Force -ErrorAction SilentlyContinue
    Expand-Archive $zip -DestinationPath $unpack
    New-Item -ItemType Directory -Force "$Sdk\cmdline-tools" | Out-Null
    Move-Item "$unpack\cmdline-tools" "$Sdk\cmdline-tools\latest"
}
Write-Host "sdkmanager: $sdkmanager"

# 2. user environment variables (no admin needed)
[Environment]::SetEnvironmentVariable("ANDROID_HOME", $Sdk, "User")
[Environment]::SetEnvironmentVariable("ANDROID_SDK_ROOT", $Sdk, "User")
$env:ANDROID_HOME = $Sdk; $env:ANDROID_SDK_ROOT = $Sdk
Write-Host "ANDROID_HOME = ANDROID_SDK_ROOT = $Sdk (user variables)"

# 3. licences (accepted by the user who runs this script) and packages
Invoke-WithRetry { ("y`n" * 20) | & $sdkmanager --sdk_root=$Sdk --licenses } "Licence acceptance"
foreach ($pkg in $Packages) {
    Invoke-WithRetry { & $sdkmanager --sdk_root=$Sdk $pkg } "Install $pkg"
}
& $sdkmanager --sdk_root=$Sdk --list_installed

# 4. portable JDK 21 for Gradle -> $Jdk
if (-not (Test-Path "$Jdk\bin\java.exe")) {
    $tmp = Join-Path $env:TEMP "jdk21-download"
    New-Item -ItemType Directory -Force $tmp | Out-Null
    $zip = Join-Path $tmp "microsoft-jdk-21.zip"
    Invoke-WithRetry {
        & curl.exe -fL --retry 3 --retry-delay 10 -o "$zip.sha256" "$JdkUrl.sha256sum.txt"
        & curl.exe -fL --retry 3 --retry-delay 10 -C - -o $zip $JdkUrl
        $expected = ((Get-Content "$zip.sha256" -Raw).Trim() -split "\s+")[0].ToLower()
        $hash = (Get-FileHash $zip -Algorithm SHA256).Hash.ToLower()
        if ($hash -ne $expected) { Remove-Item $zip; throw "SHA-256 mismatch ($hash vs $expected)" }
    } "Download of JDK 21"
    $unpack = Join-Path $tmp "unpacked"
    Remove-Item $unpack -Recurse -Force -ErrorAction SilentlyContinue
    Expand-Archive $zip -DestinationPath $unpack
    Move-Item (Get-ChildItem $unpack -Directory | Select-Object -First 1).FullName $Jdk
}
& "$Jdk\bin\java.exe" -version
