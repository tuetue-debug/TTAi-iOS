param([string]$Service,[string]$EnvString)
$workspaceNssm = 'C:\Users\vannt-pc\.openclaw\workspace\tools\nssm.exe'
$legacyNssm = 'C:\TTAi-Deployment\tools\nssm.exe'
$exe = if (Test-Path $workspaceNssm) { $workspaceNssm } elseif (Test-Path $legacyNssm) { $legacyNssm } else { $null }
if (-not $exe) { Write-Error "nssm.exe not found in workspace or legacy path"; exit 1 }
& $exe set $Service AppEnvironmentExtra $EnvString
