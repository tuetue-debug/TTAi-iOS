# Restart TTAiFastAPI8000 service
$serviceName = "TTAiFastAPI8000"

Write-Host "Stopping $serviceName..." -ForegroundColor Yellow
& "C:\Program Files\nssm\nssm.exe" stop $serviceName confirm
Start-Sleep -Seconds 3

Write-Host "Starting $serviceName..." -ForegroundColor Yellow
& "C:\Program Files\nssm\nssm.exe" start $serviceName
Start-Sleep -Seconds 5

Write-Host "Checking service status..." -ForegroundColor Cyan
& "C:\Program Files\nssm\nssm.exe" status $serviceName