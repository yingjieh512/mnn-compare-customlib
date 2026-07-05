param(
    [switch]$Execute,
    [switch]$RemoveModelAssets,
    [switch]$RemoveFinalModelZip
)

$ErrorActionPreference = "Stop"

$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

function Resolve-InWorkspace([string]$RelativePath) {
    $candidate = Join-Path $root $RelativePath
    if (-not (Test-Path -LiteralPath $candidate)) {
        return $null
    }
    $resolved = (Resolve-Path -LiteralPath $candidate).Path
    if (-not ($resolved.Equals($root, [System.StringComparison]::OrdinalIgnoreCase) -or
              $resolved.StartsWith($root + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase))) {
        throw "Refusing to clean path outside workspace: $resolved"
    }
    return $resolved
}

function Get-PathSizeBytes([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) {
        return 0
    }
    $item = Get-Item -LiteralPath $Path -Force
    if (-not $item.PSIsContainer) {
        return [int64]$item.Length
    }
    $sum = (Get-ChildItem -LiteralPath $Path -Force -Recurse -File -ErrorAction SilentlyContinue |
        Measure-Object -Property Length -Sum).Sum
    if ($null -eq $sum) {
        return 0
    }
    return [int64]$sum
}

function Remove-PathWithRetry([string]$Path, [string]$RelativePath) {
    $lastError = $null
    for ($attempt = 1; $attempt -le 5; $attempt++) {
        try {
            Remove-Item -LiteralPath $Path -Recurse -Force -ErrorAction Stop
            Write-Host ("Deleted {0}" -f $RelativePath)
            return
        } catch {
            $lastError = $_
            if ($attempt -lt 5) {
                Start-Sleep -Milliseconds (250 * $attempt)
            }
        }
    }
    Write-Warning ("Skipped {0}: {1}" -f $RelativePath, $lastError.Exception.Message)
}

$deleteRelative = @(
    "build",
    "build-host",
    "build-android-check",
    "build-host-opt",
    ".gradle",
    ".venv-export",
    "android/app/build",
    "android/app/.cxx",
    "android/benchmark_app/build",
    "android/benchmark_app/.cxx",
    "results/raw",
    "results/reports/qwen35_9b_full_custom_v16_presentation",
    "results/reports/qwen35_9b_devicefarm_v14_hotpath_presentation",
    "results/reports/qwen35_9b_kernel_library_walkthrough_devicefarm_v13",
    "results/reports/qwen35_9b_full_custom_v16_presentation.pptx.inspect.ndjson",
    "results/reports/qwen35_9b_devicefarm_v14_hotpath_presentation.pptx.inspect.ndjson",
    "results/reports/qwen35_9b_kernel_library_walkthrough_devicefarm_v13.pptx.inspect.ndjson"
)

if ($RemoveModelAssets) {
    $deleteRelative += @("models", "out")
} else {
    $deleteRelative += @(
        "out/devicefarm_private",
        "out/devicefarm_specs",
        "out/devicefarm_specs_private",
        "out/private_devicefarm_specs",
        "out/qwen35_custom_w4",
        "out/qwen35_mnn_skip",
        "out/qwen35_xq_fullcustom_v15",
        "out/qwen35_xq_fullcustom_v15_parts",
        "out/qwen35_xq_fullcustom_v17_parts",
        "out/qwen35_xq_hotpath",
        "out/qwen35_xq_hotpath_parts_v14",
        "out/qwen35_xq_hotpath_test",
        "out/tmp_probe",
        "out/old_custom_split_fullcustom_v16_measured3.yml",
        "out/qwen35_mnn_skip.zip",
        "out/qwen35_mnn_skip_no_embeddings.zip",
        "out/qwen35_xq_hotpath.zip"
    )
    if ($RemoveFinalModelZip) {
        $deleteRelative += "out/qwen35_xq_fullcustom_v15.zip"
    }
}

$targets = @()
foreach ($relative in $deleteRelative) {
    $resolved = Resolve-InWorkspace $relative
    if ($null -ne $resolved) {
        $targets += [PSCustomObject]@{
            RelativePath = $relative
            FullPath = $resolved
            SizeBytes = Get-PathSizeBytes $resolved
        }
    }
}

$total = ($targets | Measure-Object -Property SizeBytes -Sum).Sum
if ($null -eq $total) {
    $total = 0
}

Write-Host ("Workspace: {0}" -f $root)
Write-Host ("Mode: {0}" -f ($(if ($Execute) { "EXECUTE" } else { "DRY-RUN" })))
Write-Host ("Planned cleanup: {0:N2} GB across {1} paths" -f ($total / 1GB), $targets.Count)
$targets | Sort-Object SizeBytes -Descending | ForEach-Object {
    Write-Host ("{0,9:N1} MB  {1}" -f ($_.SizeBytes / 1MB), $_.RelativePath)
}

if (-not $Execute) {
    Write-Host "Dry-run only. Re-run with -Execute to delete these paths."
    exit 0
}

foreach ($target in $targets) {
    if (Test-Path -LiteralPath $target.FullPath) {
        Remove-PathWithRetry $target.FullPath $target.RelativePath
    }
}

Write-Host "Cleanup complete."
