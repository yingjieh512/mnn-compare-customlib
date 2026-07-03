param()

$sdk = $env:ANDROID_HOME
if (-not $sdk) { $sdk = $env:ANDROID_SDK_ROOT }
if (-not $sdk) { $sdk = Join-Path $env:LOCALAPPDATA "Android\Sdk" }
if (-not (Test-Path $sdk)) {
  throw "Android SDK not found. Set ANDROID_HOME or ANDROID_SDK_ROOT."
}

$ndk = $env:ANDROID_NDK_HOME
if (-not $ndk) {
  $ndkRoot = Join-Path $sdk "ndk"
  $ndk = Get-ChildItem $ndkRoot -Directory | Sort-Object Name -Descending | Select-Object -First 1 -ExpandProperty FullName
}
if (-not (Test-Path $ndk)) {
  throw "Android NDK not found under $sdk"
}

$cmake = Get-ChildItem (Join-Path $sdk "cmake") -Filter cmake.exe -Recurse | Sort-Object FullName -Descending | Select-Object -First 1 -ExpandProperty FullName
if (-not $cmake) {
  throw "Android SDK CMake not found under $sdk"
}

[pscustomobject]@{
  ANDROID_HOME = $sdk
  ANDROID_NDK_HOME = $ndk
  CMAKE = $cmake
}

