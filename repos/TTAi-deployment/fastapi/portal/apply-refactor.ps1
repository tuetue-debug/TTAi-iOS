# Apply refactored files
$src = "refactored"
$pages = Join-Path $src "pages"
$components = Join-Path $src "components"

if (Test-Path $pages) { Copy-Item "$pages\*" "src\pages\" -Force }
if (Test-Path $components) { Copy-Item "$components\*" "src\components\" -Force }

Write-Host "Applied refactored files"
