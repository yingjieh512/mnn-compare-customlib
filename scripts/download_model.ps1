param(
  [string]$OutDir = "models\Qwen3.5-9B"
)

$ErrorActionPreference = "Stop"
$revision = "c202236235762e1c871ad0ccb60c8ee5ba337b9a"

New-Item -ItemType Directory -Force (Split-Path $OutDir -Parent) | Out-Null

$hf = Get-Command huggingface-cli -ErrorAction SilentlyContinue
if ($hf) {
  & $hf.Source download Qwen/Qwen3.5-9B --revision $revision --local-dir $OutDir --local-dir-use-symlinks False
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
  exit 0
}

$lfs = Get-Command git-lfs -ErrorAction SilentlyContinue
if (-not $lfs) {
  throw "Install huggingface-cli or git-lfs to download Qwen/Qwen3.5-9B."
}

git lfs install
if (-not (Test-Path (Join-Path $OutDir ".git"))) {
  git clone https://huggingface.co/Qwen/Qwen3.5-9B $OutDir
}
git -C $OutDir checkout $revision
git -C $OutDir lfs pull

