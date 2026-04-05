param(
    [Alias('ServiceName')]
    [string]$Service,
    [string]$Key
)

$candidates = @(
    'C:\TTAi-Deployment\tools\nssm.exe',
    'C:\Users\vannt-pc\.openclaw\workspace\tools\nssm.exe',
    'C:\Users\vannt-pc\.openclaw\workspace\automation\tools\nssm.exe',
    'C:\ProgramData\chocolatey\bin\nssm.exe',
    'C:\Windows\System32\nssm.exe'
)

$exe = $candidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $exe) {
    $cmd = Get-Command nssm.exe -ErrorAction SilentlyContinue
    if ($cmd) {
        $exe = $cmd.Source
    }
}

if (-not $exe) {
    Write-Error "nssm.exe not found in known locations or PATH. Checked: $($candidates -join ', ')"
    exit 1
}

if (-not $Service) {
    Write-Error "Missing -Service (or -ServiceName) argument"
    exit 1
}
if (-not $Key) {
    Write-Error "Missing -Key argument"
    exit 1
}

& $exe get $Service $Key
