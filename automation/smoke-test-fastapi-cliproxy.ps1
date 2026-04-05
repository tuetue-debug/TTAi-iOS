param(
    [string]$FastApiUrl = 'http://127.0.0.1:8000',
    [string]$CliProxyUrl = 'https://127.0.0.1:8317',
    [string]$CliProxyApiKey = 'cliproxy-dev-token',
    [string]$UserId = 'smoke_test_fastapi_cliproxy'
)

$ErrorActionPreference = 'Stop'

Write-Host '== 1) FastAPI health ==' -ForegroundColor Cyan
curl.exe -s -D - "$FastApiUrl/health"

Write-Host "`n== 2) CLIProxy models ==" -ForegroundColor Cyan
curl.exe -k -s -D - "$CliProxyUrl/v1/models" -H "Authorization: Bearer $CliProxyApiKey"

Write-Host "`n== 3) FastAPI /api/chat ==" -ForegroundColor Cyan
$body = @{
    message = 'Smoke test metering and CLI proxy integration'
    user_id = $UserId
    use_memory = $false
} | ConvertTo-Json

Invoke-RestMethod -Uri "$FastApiUrl/api/chat" `
    -Method POST `
    -ContentType 'application/json' `
    -Body $body | ConvertTo-Json -Depth 8

Write-Host "`n== 4) Latest usage events ==" -ForegroundColor Cyan
Get-Content 'C:\Users\vannt-pc\.openclaw\workspace\repos\TTAi-deployment\fastapi\data\usage_events.jsonl' | Select-Object -Last 3
