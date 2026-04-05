param(
    [string]$Workspace = "$env:USERPROFILE/.openclaw/workspace"
)

$ErrorActionPreference = 'Stop'
$dateStamp = (Get-Date -Format 'yyyy-MM-dd')
$timeStamp = (Get-Date -Format 'yyyyMMdd-HHmmss')
$memoryDir = Join-Path $Workspace 'memory'
$logsDir = Join-Path $Workspace 'logs'
$stateDir = Join-Path $env:USERPROFILE '.openclaw'
$memoryDb = Join-Path $stateDir 'memory/main.sqlite'
$backupRoot = Join-Path $memoryDir 'backups'
$logSource = Join-Path $env:LOCALAPPDATA "Temp/openclaw/openclaw-$dateStamp.log"
$sqliteRetentionDays = 3
$logRetentionDays = 3

if (!(Test-Path $memoryDir)) {
    throw "Memory directory not found: $memoryDir"
}

if (!(Test-Path $backupRoot)) {
    New-Item -ItemType Directory -Path $backupRoot | Out-Null
}

$todayFile = Join-Path $memoryDir "$dateStamp.md"
if (!(Test-Path $todayFile)) {
    "# $dateStamp" | Out-File -FilePath $todayFile -Encoding utf8
}

if (Test-Path $memoryDb) {
    $dbBackup = Join-Path $backupRoot "main-$timeStamp.sqlite"
    Copy-Item $memoryDb $dbBackup -Force

    Get-ChildItem -Path $backupRoot -Filter 'main-*.sqlite' -File -ErrorAction SilentlyContinue |
        Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-$sqliteRetentionDays) } |
        Remove-Item -Force -ErrorAction SilentlyContinue
}

$mdBackupDir = Join-Path $backupRoot $dateStamp
if (!(Test-Path $mdBackupDir)) {
    New-Item -ItemType Directory -Path $mdBackupDir | Out-Null
}

Get-ChildItem -Path $memoryDir -Filter '*.md' -File | ForEach-Object {
    Copy-Item $_.FullName (Join-Path $mdBackupDir $_.Name) -Force
}

Get-ChildItem -Path $backupRoot -Directory -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -match '^\d{4}-\d{2}-\d{2}$' -and $_.LastWriteTime -lt (Get-Date).AddDays(-$sqliteRetentionDays) } |
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

# Backup agent log locally (similar to memory)
$localLogBackupDir = Join-Path $logsDir "backups/$dateStamp"
if (!(Test-Path $localLogBackupDir)) {
    New-Item -ItemType Directory -Path $localLogBackupDir -Force | Out-Null
}
if (Test-Path $logSource) {
    $logTarget = Join-Path $localLogBackupDir "openclaw-$dateStamp-$timeStamp.log"
    Copy-Item $logSource $logTarget -Force

    Get-ChildItem -Path (Join-Path $logsDir 'backups') -Recurse -File -ErrorAction SilentlyContinue |
        Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-$logRetentionDays) } |
        Remove-Item -Force -ErrorAction SilentlyContinue
}

$kbSource = $env:TTAI_KB_PATH
if ($kbSource -and (Test-Path $kbSource)) {
    $kbBackupRoot = 'E:/openclaw-backup/knowledge_base'
    if (!(Test-Path $kbBackupRoot)) {
        New-Item -ItemType Directory -Path $kbBackupRoot -Force | Out-Null
    }
    $kbBackupDir = Join-Path $kbBackupRoot $dateStamp
    if (!(Test-Path $kbBackupDir)) {
        New-Item -ItemType Directory -Path $kbBackupDir -Force | Out-Null
    }
    robocopy $kbSource $kbBackupDir /MIR /NFL /NDL /NJH /NJS | Out-Null
}

Write-Host "Memory + log verified and backed up (local)"
