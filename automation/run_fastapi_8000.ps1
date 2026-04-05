$ErrorActionPreference = 'Stop'

$workspaceRoot = 'C:\Users\vannt-pc\.openclaw\workspace'
$appRoot = Join-Path $workspaceRoot 'repos\TTAi-deployment\fastapi'
$pythonExe = Join-Path $env:LocalAppData 'Programs\Python\Python311\python.exe'
$logDir = Join-Path $appRoot 'logs'
$stdoutLog = Join-Path $logDir 'fastapi_8000_stdout.log'
$stderrLog = Join-Path $logDir 'fastapi_8000_stderr.log'

if (-not (Test-Path $pythonExe)) {
    throw "Python not found at $pythonExe"
}

New-Item -ItemType Directory -Force -Path $logDir | Out-Null
Set-Location $appRoot

Write-Host "[run_fastapi_8000] app root: $appRoot"
Write-Host "[run_fastapi_8000] python: $pythonExe"
Write-Host "[run_fastapi_8000] starting uvicorn on port 8000..."

& $pythonExe -m uvicorn main:app --host 0.0.0.0 --port 8000 2>> $stderrLog | Tee-Object -FilePath $stdoutLog -Append
