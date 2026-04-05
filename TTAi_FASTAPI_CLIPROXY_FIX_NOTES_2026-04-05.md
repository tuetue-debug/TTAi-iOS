# TTAi FastAPI + CLIProxy Fix Notes — 2026-04-05

## Summary
This note captures the end-to-end debugging and fix path for FastAPI port 8000, CLIProxy integration, and usage metering validation.

## Initial Symptoms
- `POST /api/chat` on FastAPI 8000 failed even when the Windows service was running.
- Usage metering events were partially recorded, but requests returned errors.
- PowerShell sometimes showed generic `Unable to connect to the remote server`, which masked the app-level error.

## Root Causes Found
1. **PowerShell JSON quoting problems**
   - `curl.exe` inside PowerShell broke JSON payloads easily.
   - Preferred approach: `Invoke-RestMethod` + `ConvertTo-Json`.

2. **Missing `ProviderType` import in `repos/TTAi-deployment/fastapi/main.py`**
   - `main.py` referenced `ProviderType` but did not import it.
   - Fix: import `ProviderType` from `load_balancer`.

3. **Public CLI proxy endpoint was not usable from the local machine**
   - `https://vannt.vinaddns.com:8317` resolved to the public IP but local connection attempts were refused.
   - Local service-to-service calls should not depend on the public route.

4. **Local HTTPS certificate mismatch on `127.0.0.1`**
   - `https://127.0.0.1:8317` reached the local CLI proxy, but TLS verification failed because the certificate did not match the IP hostname.
   - Fix: use local endpoint with `verify=False` in the FastAPI `httpx.AsyncClient` for internal CLI proxy calls.

5. **CLIProxy model/provider mapping issue**
   - DeepSeek alias config in `CLIProxyAPI/config.yaml` needed correction.
   - The working path in the final flow used `gpt-mini` while the provider remained `cliproxy-deepseek` in metering output.

6. **Missing FastAPI service auth token for CLI proxy**
   - FastAPI only sends Authorization if `CLI_PROXY_API_KEY` exists in the service environment.
   - Fix: set `CLI_PROXY_API_KEY=cliproxy-dev-token` in the `TTAiFastAPI8000` NSSM service environment.

7. **Broken automation script for setting service env**
   - `automation/set_service_env.ps1` hardcoded an outdated NSSM path.
   - Fix: update the script to prefer `C:\Users\vannt-pc\.openclaw\workspace\tools\nssm.exe` and fall back to legacy path.

## Runtime Configuration That Worked
### FastAPI 8000
- CLI proxy URL path in code uses:
  - `https://127.0.0.1:8317`
- Internal HTTPS calls use:
  - `httpx.AsyncClient(..., verify=False)`
- CLI proxy auth token is read from:
  - `CLI_PROXY_API_KEY`

### Required service environment
Minimum required env for `TTAiFastAPI8000`:

```text
CLI_PROXY_API_KEY=cliproxy-dev-token
```

### CLIProxy
- Service: `TTAiCLIProxy`
- Local API on port `8317`
- `/v1/models` returned `200 OK`
- End-to-end `/api/chat` worked after FastAPI service env was fixed

## Verification Steps
### 1) Check FastAPI service health
```powershell
Get-Service TTAiFastAPI8000
curl.exe -s -D - http://127.0.0.1:8000/health
```

### 2) Check CLI proxy local health/models
```powershell
curl.exe -k https://127.0.0.1:8317/v1/models -H "Authorization: Bearer cliproxy-dev-token"
```

### 3) Test end-to-end chat
```powershell
$body = @{
  message = "test"
  user_id = "smoke_test"
  use_memory = $false
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/chat" `
  -Method POST `
  -ContentType "application/json" `
  -Body $body
```

### 4) Confirm usage metering
```powershell
Get-Content C:\Users\vannt-pc\.openclaw\workspace\repos\TTAi-deployment\fastapi\data\usage_events.jsonl | Select-Object -Last 3
```

Expected success indicators:
- `status: success`
- `http_status: 200`

## Troubleshooting Order For Future Incidents
1. Check `Get-Service TTAiFastAPI8000`
2. Check `GET /health`
3. Check local CLI proxy `/v1/models`
4. Check NSSM env: `AppEnvironmentExtra`
5. Check latest lines in `usage_events.jsonl`

## Useful Commands
### Set FastAPI service env
```powershell
C:\Users\vannt-pc\.openclaw\workspace\tools\nssm.exe set TTAiFastAPI8000 AppEnvironmentExtra "CLI_PROXY_API_KEY=cliproxy-dev-token"
```

### Read FastAPI service env
```powershell
C:\Users\vannt-pc\.openclaw\workspace\tools\nssm.exe get TTAiFastAPI8000 AppEnvironmentExtra
```

### Restart services
```powershell
Restart-Service TTAiCLIProxy
Restart-Service TTAiFastAPI8000
```

## Git Reference
Main fix commit:

```text
3823a0f Fix FastAPI CLI proxy integration
```

## Outcome
- FastAPI `/api/chat` succeeded end-to-end
- Usage metering schema remained active and logged successful events
- CLI proxy auth and local connectivity issues were resolved
