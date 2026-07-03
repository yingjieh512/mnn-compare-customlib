param(
  [string]$GradleBat = ""
)

$ErrorActionPreference = "Stop"
$root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $root

$sdkInfo = & (Join-Path $PSScriptRoot "find_android_sdk.ps1")
$env:ANDROID_HOME = $sdkInfo.ANDROID_HOME
$env:ANDROID_SDK_ROOT = $sdkInfo.ANDROID_HOME
$env:ANDROID_NDK_HOME = $sdkInfo.ANDROID_NDK_HOME

if (-not $GradleBat) {
  if (Test-Path ".\gradlew.bat") {
    $GradleBat = ".\gradlew.bat"
  } else {
    $candidate = Get-ChildItem "$env:USERPROFILE\.gradle\wrapper\dists" -Filter gradle.bat -Recurse -ErrorAction SilentlyContinue |
      Where-Object { $_.FullName -match "gradle-8\." } |
      Select-Object -First 1 -ExpandProperty FullName
    if (-not $candidate) {
      $candidate = Get-ChildItem "$env:USERPROFILE\.gradle\wrapper\dists" -Filter gradle.bat -Recurse -ErrorAction SilentlyContinue |
        Select-Object -First 1 -ExpandProperty FullName
    }
    if ($candidate) { $GradleBat = $candidate }
  }
}

if (-not $GradleBat) {
  throw "No Gradle executable found. Install Gradle 8.7 or add a Gradle wrapper jar."
}

& $GradleBat `
  ":stock_mnn_benchmark:assembleDebug" `
  ":stock_mnn_benchmark:assembleRelease" `
  ":stock_mnn_benchmark:assembleAndroidTest" `
  ":customlib_benchmark:assembleDebug" `
  ":customlib_benchmark:assembleRelease" `
  ":customlib_benchmark:assembleAndroidTest"

if ($LASTEXITCODE -ne 0) {
  exit $LASTEXITCODE
}
