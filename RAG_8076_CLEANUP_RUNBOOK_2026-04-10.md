# RAG 8076 Cleanup Runbook — 2026-04-10

## Purpose
Clean up the temporary proof service on `8076` after the canonical `8075` runtime has been validated successfully.

---

## Step 1 — Check whether 8076 is still listening
```powershell
Get-NetTCPConnection -LocalPort 8076 -State Listen
```

## Step 2 — Inspect the holder
```powershell
Get-CimInstance Win32_Process -Filter "ProcessId = <PID>" | Select-Object ProcessId, ParentProcessId, Name, ExecutablePath, CommandLine | Format-List
```

## Step 3 — Stop the proof holder
```powershell
Stop-Process -Id <PID> -Force
Start-Sleep -Seconds 3
```

## Step 4 — Confirm cleanup
```powershell
Get-NetTCPConnection -LocalPort 8076 -State Listen
```
Expected result: no listener.

---

## Rule
Do not leave the proof service running longer than needed once the canonical 8075 runtime is confirmed healthy.
