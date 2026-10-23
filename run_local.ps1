param([string]$PythonBin)
$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot
if (-not $PythonBin) {
    $PythonBin = (Get-Command python -ErrorAction Stop).Source
}
$packages = Join-Path $PSScriptRoot "runtime\packages"
if (Test-Path -LiteralPath $packages) { $env:PYTHONPATH = "$packages;$env:PYTHONPATH" }
$localAccess = Join-Path $PSScriptRoot "runtime\access.local.json"
if (Test-Path -LiteralPath $localAccess) {
    $access = Get-Content -LiteralPath $localAccess -Raw | ConvertFrom-Json
    $env:MONGO_USER = "libWriter"
    $env:MONGO_PASSWORD = $access.libWriter
}
$env:PYTHONIOENCODING = "utf-8"
try { & $PythonBin main.py }
finally { Remove-Item Env:MONGO_PASSWORD -ErrorAction SilentlyContinue }
