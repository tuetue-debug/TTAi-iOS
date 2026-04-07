# Restart TTAiFastAPI8000 service
$serviceName = "TTAiFastAPI8000"
$workspaceNssm = "C:\Users\vannt-pc\.openclaw\workspace\tools\nssm.exe"
$legacyNssm = "C:\Program Files\nssm\nssm.exe"

if (Test-Path $workspaceNssm) {
    $nssm = $workspaceNssm
} elseif (Test-Path $legacyNssm) {
    $nssm = $legacyNssm
} else {
    Write-Error "NSSM not found. Checked: $workspaceNssm and $legacyNssm"
    exit 1
}

Write-Host "Using NSSM: $nssm" -ForegroundColor Cyan

Write-Host "Stopping $serviceName..." -ForegroundColor Yellow
& $nssm stop $serviceName confirm
Start-Sleep -Seconds 3

Write-Host "Starting $serviceName..." -ForegroundColor Yellow
& $nssm start $serviceName
Start-Sleep -Seconds 5

Write-Host "Checking service status..." -ForegroundColor Cyan
& $nssm status $serviceName
