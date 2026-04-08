import sys
import json
import asyncio
import uuid
import httpx
from pathlib import Path

sys.path.insert(0, r"C:\Users\vannt-pc\.openclaw\workspace\repos\TTAi-deployment\fastapi")
import main  # noqa: E402

USAGE_PATH = Path(r"C:\Users\vannt-pc\.openclaw\workspace\repos\TTAi-deployment\fastapi\data\usage_events.jsonl")


def read_recent(limit=20):
    if not USAGE_PATH.exists():
        return []
    lines = USAGE_PATH.read_text(encoding="utf-8").splitlines()
    out = []
    for line in lines[-limit:]:
        if not line.strip():
            continue
        try:
            out.append(json.loads(line))
        except Exception:
            pass
    return out


async def run():
    before = read_recent(20)
    before_ids = {item.get("request_id") for item in before}

    transport = httpx.ASGITransport(app=main.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        email = f"debug_link_{uuid.uuid4().hex[:8]}@example.com"
        password = "SmokePass123!"
        out = {"email": email}

        r = await client.post("/api/v1/auth/register", json={
            "name": "Debug User",
            "email": email,
            "password": password,
        })
        out["register_status"] = r.status_code
        reg = r.json()
        out["register_body"] = reg
        access = reg.get("access_token")
        user = reg.get("user") or {}
        hdr = {"Authorization": f"Bearer {access}"}

        r_key = await client.post("/api/v1/account/api-keys", headers=hdr, json={
            "name": "Debug Key",
            "scopes": ["chat:write"],
        })
        out["api_key_create_status"] = r_key.status_code
        key_body = r_key.json()
        out["api_key_create_body"] = key_body
        raw_key = key_body.get("key")
        key_id = key_body.get("id")

        r_me = await client.get("/api/v1/auth/api-key/me", headers={"X-API-Key": raw_key})
        out["api_key_me_status"] = r_me.status_code
        out["api_key_me_body"] = r_me.json()

        r_chat = await client.post("/api/v1/chat", headers={"X-API-Key": raw_key}, json={
            "message": "Hello from API key debug pass"
        })
        out["chat_status"] = r_chat.status_code
        out["chat_body"] = r_chat.json()

        usage_resp = await client.get("/api/v1/account/usage/events", headers=hdr)
        out["usage_events_status"] = usage_resp.status_code
        out["usage_events_body"] = usage_resp.json()

        billing_resp = await client.get("/api/v1/account/billing/summary", headers=hdr)
        out["billing_summary_status"] = billing_resp.status_code
        out["billing_summary_body"] = billing_resp.json()

        after = read_recent(30)
        new_events = [item for item in after if item.get("request_id") not in before_ids]
        out["new_usage_events"] = new_events
        out["expected"] = {
            "user_id": user.get("id"),
            "api_key_id": key_id,
        }

        print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(run())
