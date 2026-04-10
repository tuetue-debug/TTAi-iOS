param(
    [switch]$SkipReindex,
    [switch]$SkipRag
)

$ErrorActionPreference = 'Stop'

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$workspace = Split-Path -Parent $scriptDir
$logsDir = Join-Path $workspace 'logs'
if (-not (Test-Path $logsDir)) {
    New-Item -ItemType Directory -Path $logsDir | Out-Null
}

function Invoke-ReindexPhase {
    param([string]$ScriptPath)
    Write-Host "[Nightly] Starting legacy memory reindex via $ScriptPath" -ForegroundColor Cyan
    & $ScriptPath
    $exit = $LASTEXITCODE
    if ($exit -ne 0) {
        throw "Legacy memory reindex failed with exit code $exit"
    }
    Write-Host "[Nightly] Legacy memory reindex complete" -ForegroundColor Green
}

function Invoke-RagPhase {
    param(
        [string]$Workspace,
        [string]$LogFile,
        [string]$IngestScript = '.\\TTAi-AI-Model\\rag_engine.py'
    )

    $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    Add-Content -Path $LogFile -Value "`n[$timestamp] Starting RAG ingest"

    Push-Location $Workspace
    $prevErrorPreference = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        Write-Host "[Nightly] RAG ingest target script: $IngestScript" -ForegroundColor DarkCyan
        $ragOutput = & python $IngestScript 2>&1
        $exit = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $prevErrorPreference
        Pop-Location
    }

    $ragOutput | Tee-Object -FilePath $LogFile -Append | Out-Null

    if ($exit -ne 0) {
        Add-Content -Path $LogFile -Value "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] RAG ingest FAILED (exit code $exit)"
        throw "RAG ingest failed with exit code $exit"
    }

    Add-Content -Path $LogFile -Value "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] RAG ingest completed"
    Write-Host "[Nightly] RAG ingest complete" -ForegroundColor Green
}

try {
    if (-not $SkipReindex) {
        $reindexScript = Join-Path $scriptDir 'no-downtime-memory-reindex.ps1'
        if (-not (Test-Path $reindexScript)) {
            throw "Reindex script not found at $reindexScript"
        }
        Invoke-ReindexPhase -ScriptPath $reindexScript
    } else {
        Write-Host "[Nightly] Skipping legacy memory reindex" -ForegroundColor Yellow
    }

    if (-not $SkipRag) {
        $ragLog = Join-Path $logsDir 'rag_ingest.log'
        Invoke-RagPhase -Workspace $workspace -LogFile $ragLog -IngestScript '.\\TTAi-AI-Model\\rag_engine.py'
    } else {
        Write-Host "[Nightly] Skipping RAG ingest" -ForegroundColor Yellow
    }

    Write-Host "[Nightly] Memory + RAG refresh succeeded" -ForegroundColor Green
}
catch {
    Write-Error $_
    exit 1
}
