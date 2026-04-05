$ErrorActionPreference = 'Stop'

$workspaceRoot = 'C:\Users\vannt-pc\.openclaw\workspace'
$appRoot = Join-Path $workspaceRoot 'repos\TTAi-deployment\fastapi'
$pythonExe = Join-Path $env:LocalAppData 'Programs\Python\Python311\python.exe'
$runScript = Join-Path $workspaceRoot 'automation\run_fastapi_8000.ps1'

Write-Host '[restart_fastapi_8000] stopping existing uvicorn main:app :8000 processes if any...'
Get-CimInstance Win32_Process | Where-Object {
    $_.CommandLine -like '*uvicorn main:app*8000*'
} | ForEach-Object {
    try {
        Stop-Process -Id $_.ProcessId -Force -ErrorAction Stop
        Write-Host "Stopped PID $($_.ProcessId)"
    } catch {
        Write-Warning "Could not stop PID $($_.ProcessId): $_"
    }
}

Start-Sleep -Seconds 2

Write-Host '[restart_fastapi_8000] starting new process...'
Start-Process powershell -ArgumentList '-ExecutionPolicy','Bypass','-File',$runScript -WorkingDirectory $appRoot

Start-Sleep -Seconds 5

Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue |
    Where-Object { $_.LocalPort -eq 8000 } |
    Select-Object LocalAddress,LocalPort,OwningProcess
