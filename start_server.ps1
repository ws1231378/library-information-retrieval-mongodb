param([switch]$Auth, [switch]$EnableTTL, [string]$MongoBin)
$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
if (-not $MongoBin) {
    $portable = Join-Path $root "runtime\mongo\mongod.exe"
    if (Test-Path -LiteralPath $portable) { $MongoBin = $portable }
    else { $MongoBin = (Get-Command mongod -ErrorAction Stop).Source }
}
$dataDir = Join-Path $root "runtime\db"
New-Item -ItemType Directory -Force -Path $dataDir | Out-Null
$logPath = Join-Path $root "runtime\mongod.log"
$mongoArgs = @("--dbpath", $dataDir, "--bind_ip", "127.0.0.1", "--port", "27017",
               "--wiredTigerCacheSizeGB", "0.25", "--logpath", $logPath, "--logappend")
if ($Auth) { $mongoArgs += "--auth" }
if (-not $EnableTTL) {
    Write-Host "实训历史数据模式：暂停TTL自动清理，集合仍配置两年过期。"
    $mongoArgs += @("--setParameter", "ttlMonitorEnabled=false")
}
Write-Host "数据目录：$dataDir"
Write-Host "端口：27017；仅本机访问。请保持此终端运行。"
& $MongoBin @mongoArgs
