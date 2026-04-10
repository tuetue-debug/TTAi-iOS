param(
    [string]$ServiceName = "TTAiRagService",
    [string]$Workspace = "C:\\Users\\vannt-pc\\.openclaw\\workspace",
    [string]$ScriptRelativePath = "services\\rag_service\\rag_service.py",
    [string]$PythonPath = "",
    [string]$NssmPath = "tools\\nssm.exe"
)

Write-Host "Registering stable 8075 compatibility surface for RAG service" -ForegroundColor Cyan

function Get-PythonExecutable {
    param([string]$Workspace)
    $candidates = @(
        (Join-Path $Workspace "venv\\Scripts\\python.exe"),
        "$env:LOCALAPPDATA\\Programs\\Python\\Python311\\python.exe",
        "$env:LOCALAPPDATA\\Programs\\Python\\Python312\\python.exe",
        "C:\\Program Files\\Python311\\python.exe",
        "C:\\Program Files\\Python312\\python.exe",
        "python.exe"
    )
    foreach ($candidate in $candidates) {
        try {
            if ($candidate -like "*.exe" -and (Test-Path $candidate)) {
                return $candidate
            }
            $cmd = Get-Command $candidate -ErrorAction Stop
            if ($cmd) { return $cmd.Source }
        } catch {
            continue
        }
    }
    throw "Unable to locate python executable. Specify -PythonPath manually."
}

$workspacePath = (Resolve-Path $Workspace).Path
$scriptPath = Join-Path $workspacePath $ScriptRelativePath
if (-not (Test-Path $scriptPath)) {
    throw "RAG service compatibility surface script not found at $scriptPath"
}

if (-not $PythonPath) {
    $PythonPath = Get-PythonExecutable -Workspace $workspacePath
}

if (-not (Test-Path $PythonPath)) {
    throw "Python executable not found at $PythonPath"
}

if (-not (Test-Path $NssmPath)) {
    throw "nssm.exe not found at $NssmPath. Run download_nssm.ps1 first."
}

$logDir = Join-Path $workspacePath "logs\\rag_service"
New-Item -ItemType Directory -Path $logDir -Force | Out-Null

Write-Host "Installing $ServiceName using $PythonPath" -ForegroundColor Cyan

& $NssmPath stop $ServiceName 2>$null | Out-Null
& $NssmPath remove $ServiceName confirm 2>$null | Out-Null

& $NssmPath install $ServiceName $PythonPath $scriptPath
& $NssmPath set $ServiceName AppDirectory $workspacePath
& $NssmPath set $ServiceName AppStdout (Join-Path $logDir "stdout.log")
& $NssmPath set $ServiceName AppStderr (Join-Path $logDir "stderr.log")
& $NssmPath set $ServiceName Start SERVICE_AUTO_START
& $NssmPath set $ServiceName AppPriority HIGH_PRIORITY_CLASS

Write-Host "Starting service..." -ForegroundColor Yellow
& $NssmPath start $ServiceName
Write-Host "$ServiceName is now managed by NSSM as the stable 8075 compatibility surface." -ForegroundColor Green
