# RAG 8075 Orphan Process Recovery Runbook — 2026-04-10

## Situation
Port `8075` is currently owned by Python PID `7696`, which is not a child of the current `TTAiRagService` NSSM process.

This means service-level configuration changes do not control the actual live runtime on `8075` until that orphan holder is removed.

---

## Goal
Cleanly remove the orphan holder of `8075`, then let the canonical runner owned by `TTAiRagService` bind the port.

---

## Step 1 — Verify the live holder
```powershell
Get-NetTCPConnection -LocalPort 8075 -State Listen
```
Expected owner before cleanup: `7696`

---

## Step 2 — Inspect the holder
```powershell
Get-CimInstance Win32_Process -Filter "ProcessId = 7696" | Select-Object ProcessId, ParentProcessId, Name, ExecutablePath, CommandLine | Format-List
```

---

## Step 3 — Stop the managed service first
```powershell
$env:NSSM="C:\Users\vannt-pc\.openclaw\workspace\tools\nssm.exe"
& $env:NSSM stop TTAiRagService
Start-Sleep -Seconds 5
```
This avoids fighting with service restarts while reclaiming the port.

---

## Step 4 — Kill the orphan holder of 8075
```powershell
Stop-Process -Id 7696 -Force
Start-Sleep -Seconds 3
```

If the holder changes, replace `7696` with the current owner shown by `Get-NetTCPConnection`.

---

## Step 5 — Confirm the port is free
```powershell
Get-NetTCPConnection -LocalPort 8075 -State Listen
```
Expected result: no listener, or a new listener only after the service is restarted.

---

## Step 6 — Start canonical runner service
```powershell
& $env:NSSM start TTAiRagService
Start-Sleep -Seconds 6
Get-Service TTAiRagService
```

---

## Step 7 — Verify canonical ownership and proof
```powershell
Get-NetTCPConnection -LocalPort 8075 -State Listen
python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8075/build-proof').read().decode())"
python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8075/compatibility').read().decode())"
python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8075/health').read().decode())"
```

---

## Success criteria
- `TTAiRagService` is running
- port `8075` is now owned by the expected managed process
- `/build-proof` exists
- `/compatibility` reports `rag_v2`
- build marker is visible

---

## Rollback
If canonical runner still does not take over cleanly:
1. stop service
2. keep 8076 proof service as working reference
3. inspect the new 8075 owner PID again before taking more action

---

## Design lesson
A managed service is not enough unless it also owns the live port. Always verify real port ownership after cutovers.
