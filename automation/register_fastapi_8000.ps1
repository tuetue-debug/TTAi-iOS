param(
    [string]$ServiceName = 'TTAiFastAPI8000'
)

$ErrorActionPreference = 'Stop'

$workspaceRoot = 'C:\Users\vannt-pc\.openclaw\workspace'
$appRoot = Join-Path $workspaceRoot 'repos\TTAi-deployment\fastapi'
$pythonExe = Join-Path $env:LocalAppData 'Programs\Python\Python311\python.exe'
$nssmExe = Join-Path $workspaceRoot 'tools\nssm.exe'
$logDir = Join-Path $appRoot 'logs'

if (-not (Test-Path $pythonExe)) {
    throw "Python not found at $pythonExe"
}
if (-not (Test-Path $nssmExe)) {
    throw "NSSM not found at $nssmExe"
}

New-Item -ItemType Directory -Force -Path $logDir | Out-Null

& $nssmExe stop $ServiceName | Out-Null
& $nssmExe remove $ServiceName confirm | Out-Null

& $nssmExe install $ServiceName $pythonExe "-m uvicorn main:app --host 0.0.0.0 --port 8000"
& $nssmExe set $ServiceName AppDirectory $appRoot
& $nssmExe set $ServiceName AppStdout (Join-Path $logDir 'fastapi_8000_service_stdout.log')
& $nssmExe set $ServiceName AppStderr (Join-Path $logDir 'fastapi_8000_service_stderr.log')
& $nssmExe set $ServiceName Start SERVICE_AUTO_START
& $nssmExe start $ServiceName

Start-Sleep -Seconds 3
Get-Service $ServiceName | Select-Object Name,Status
