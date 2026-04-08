import sys
import json
import asyncio
import httpx

sys.path.insert(0, r"C:\Users\vannt-pc\.openclaw\workspace\repos\TTAi-deployment\fastapi")
import main  # noqa: E402


async def run():
    transport = httpx.ASGITransport(app=main.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        email = "smoke_chat_part4@example.com"
        password = "SmokePass123!"
        out = {}

        r = await client.post("/api/v1/auth/register", json={
            "name": "Chat Smoke User",
            "email": email,
            "password": password,
        })
        out["register"] = r.status_code
        auth_data = r.json()
        access = auth_data.get("access_token")
        hdr = {"Authorization": f"Bearer {access}"}

        r_key = await client.post("/api/v1/account/api-keys", headers=hdr, json={
            "name": "Chat Smoke Key",
            "scopes": ["chat:write"],
        })
        out["api_key_create"] = r_key.status_code
        key_data = r_key.json()
        raw_key = key_data.get("key")
        key_id = key_data.get("id")

        # Chat via explicit user_id path
        r_chat_user = await client.post("/api/v1/chat", json={
            "message": "Xin chào",
            "user_id": auth_data.get("user", {}).get("id"),
        })
        out["chat_user"] = r_chat_user.status_code
        out["chat_user_body_keys"] = sorted(list(r_chat_user.json().keys())) if r_chat_user.headers.get("content-type", "").startswith("application/json") else None

        usage_user = await client.get("/api/v1/account/usage/events", headers=hdr)
        out["usage_events_after_user_chat"] = usage_user.status_code
        usage_user_data = usage_user.json() if usage_user.status_code == 200 else {}
        user_items = usage_user_data.get("items", [])
        out["usage_events_after_user_chat_count"] = len(user_items)
        out["latest_user_event_has_user_id"] = bool(user_items[0].get("user_id")) if user_items else False

        # Chat via API key path
        r_chat_key = await client.post("/api/v1/chat", headers={"X-API-Key": raw_key}, json={
            "message": "Hello from API key",
        })
        out["chat_api_key"] = r_chat_key.status_code
        out["chat_api_key_body_keys"] = sorted(list(r_chat_key.json().keys())) if r_chat_key.headers.get("content-type", "").startswith("application/json") else None

        usage_after_key = await client.get("/api/v1/account/usage/events", headers=hdr)
        out["usage_events_after_api_key_chat"] = usage_after_key.status_code
        usage_after_key_data = usage_after_key.json() if usage_after_key.status_code == 200 else {}
        key_items = usage_after_key_data.get("items", [])
        out["usage_events_after_api_key_chat_count"] = len(key_items)

        found_key_event = False
        found_key_event_has_api_key_id = False
        for item in key_items:
            if item.get("api_key_id") == key_id:
                found_key_event = True
                found_key_event_has_api_key_id = True
                break
        out["found_api_key_usage_event"] = found_key_event
        out["found_api_key_usage_event_has_api_key_id"] = found_key_event_has_api_key_id

        billing_summary = await client.get("/api/v1/account/billing/summary", headers=hdr)
        out["billing_summary_after_chat"] = billing_summary.status_code
        billing_data = billing_summary.json() if billing_summary.status_code == 200 else {}
        out["billing_summary_has_summary"] = isinstance(billing_data.get("summary"), dict)

        print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(run())
