# Test script for control frontend
Write-Host "Testing TTAi Control Frontend..." -ForegroundColor Cyan

$apiBase = "http://127.0.0.1:8000"

# Test 1: Check if FastAPI is running
try {
    $health = Invoke-RestMethod -Uri "$apiBase/health" -Method Get -TimeoutSec 5
    Write-Host "✓ FastAPI health: $($health.status)" -ForegroundColor Green
} catch {
    Write-Host "✗ FastAPI not responding: $_" -ForegroundColor Red
    exit 1
}

# Test 2: Check if control frontend is mounted
try {
    $control = Invoke-WebRequest -Uri "$apiBase/control/" -Method Get -TimeoutSec 5
    if ($control.StatusCode -eq 200) {
        Write-Host "✓ Control frontend mounted at /control" -ForegroundColor Green
    } else {
        Write-Host "✗ Control frontend returned HTTP $($control.StatusCode)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "✗ Control frontend not accessible: $_" -ForegroundColor Red
    Write-Host "Note: Service may need restart to mount static files" -ForegroundColor Yellow
}

# Test 3: Check topology route shell (will likely redirect to login if auth required)
try {
    $topology = Invoke-WebRequest -Uri "$apiBase/control-api/topology" -Method Get -TimeoutSec 5 -MaximumRedirection 0 -ErrorAction Stop
    Write-Host "✓ Topology API reachable with HTTP $($topology.StatusCode)" -ForegroundColor Green
} catch {
    if ($_.Exception.Response -and $_.Exception.Response.StatusCode.value__ -in 401,403) {
        Write-Host "✓ Topology API exists and is auth-protected ($($_.Exception.Response.StatusCode.value__))" -ForegroundColor Green
    } else {
        Write-Host "✗ Topology API check failed: $_" -ForegroundColor Yellow
    }
}

# Test 4: Check admin APIs are accessible (legacy bearer flow may or may not work depending on auth boundary)
$adminToken = "f6883d3eb388cff8fcad7d7952c568f6fd8995afa6f4581209215d582e2efe59"
$headers = @{
    "Authorization" = "Bearer $adminToken"
}

try {
    $overview = Invoke-RestMethod -Uri "$apiBase/api/v1/admin/overview?usage_limit=5&recent_events_limit=2" -Method Get -Headers $headers -TimeoutSec 10
    Write-Host "✓ Admin overview API accessible" -ForegroundColor Green
    Write-Host "  Health: $($overview.health.summary.status)"
    Write-Host "  Usage events: $($overview.usage.window_event_count)"
} catch {
    Write-Host "✗ Admin overview API failed: $_" -ForegroundColor Yellow
}

# Test 5: Check static assets
$assets = @("/control/style.css", "/control/app.js")
foreach ($asset in $assets) {
    try {
        $resp = Invoke-WebRequest -Uri "$apiBase$asset" -Method Head -TimeoutSec 5
        if ($resp.StatusCode -eq 200) {
            Write-Host "✓ Static asset $asset accessible" -ForegroundColor Green
        } else {
            Write-Host "✗ Static asset $asset returned HTTP $($resp.StatusCode)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "✗ Static asset $asset not accessible: $_" -ForegroundColor Yellow
    }
}

Write-Host "`nSummary:" -ForegroundColor Cyan
Write-Host "- /control/ should load the frontend shell" -ForegroundColor Yellow
Write-Host "- /control-api/topology should exist and usually require control session auth" -ForegroundColor Yellow
Write-Host "- If frontend assets fail, the FastAPI service may need restart to pick up changed static files" -ForegroundColor Yellow
Write-Host "Dashboard URL: http://127.0.0.1:8000/control/" -ForegroundColor Cyan
