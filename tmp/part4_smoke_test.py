import sys
import json
import asyncio
import httpx

sys.path.insert(0, r"C:\Users\vannt-pc\.openclaw\workspace\repos\TTAi-deployment\fastapi")
import main  # noqa: E402


async def run():
    transport = httpx.ASGITransport(app=main.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        email = "smoke_part4b@example.com"
        password = "SmokePass123!"
        new_password = "SmokePass456!"
        out = {}

        r = await client.post("/api/v1/auth/register", json={
            "name": "Smoke User",
            "email": email,
            "password": password,
        })
        out["register"] = r.status_code
        data = r.json()
        access = data.get("access_token")
        refresh = data.get("refresh_token")
        out["register_has_refresh"] = bool(refresh)

        hdr = {"Authorization": f"Bearer {access}"}
        out["me"] = (await client.get("/api/v1/auth/me", headers=hdr)).status_code
        out["sessions"] = (await client.get("/api/v1/auth/sessions", headers=hdr)).status_code

        r2 = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
        out["refresh"] = r2.status_code
        data2 = r2.json()
        access2 = data2.get("access_token")
        refresh2 = data2.get("refresh_token")

        hdr2 = {"Authorization": f"Bearer {access2}"}
        out["account_profile_get"] = (await client.get("/api/v1/account/profile", headers=hdr2)).status_code
        out["account_profile_put"] = (await client.put("/api/v1/account/profile", headers=hdr2, json={"name": "Smoke User Updated"})).status_code
        out["account_usage_summary"] = (await client.get("/api/v1/account/usage/summary", headers=hdr2)).status_code
        out["account_usage_events"] = (await client.get("/api/v1/account/usage/events", headers=hdr2)).status_code
        out["account_billing_summary"] = (await client.get("/api/v1/account/billing/summary", headers=hdr2)).status_code
        out["account_billing_limits"] = (await client.get("/api/v1/account/billing/limits", headers=hdr2)).status_code

        r3 = await client.post("/api/v1/account/api-keys", headers=hdr2, json={
            "name": "Smoke Key",
            "scopes": ["chat:write"],
        })
        out["api_key_create"] = r3.status_code
        key_data = r3.json()
        raw_key = key_data.get("key")
        key_id = key_data.get("id")
        out["api_key_has_secret"] = bool(raw_key)

        out["api_key_list"] = (await client.get("/api/v1/account/api-keys", headers=hdr2)).status_code
        out["api_key_identity"] = (await client.get("/api/v1/auth/api-key/me", headers={"X-API-Key": raw_key})).status_code if raw_key else None
        out["api_key_revoke"] = (await client.delete(f"/api/v1/account/api-keys/{key_id}", headers=hdr2)).status_code if key_id else None

        out["logout_current"] = (await client.post("/api/v1/auth/logout", headers=hdr2, json={"refresh_token": refresh2})).status_code

        r4 = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
        out["login_old_password_after_profile_update"] = r4.status_code
        data4 = r4.json()
        access3 = data4.get("access_token")
        hdr3 = {"Authorization": f"Bearer {access3}"}

        out["change_password"] = (await client.put("/api/v1/auth/change-password", headers=hdr3, json={
            "current_password": password,
            "new_password": new_password,
        })).status_code

        r5 = await client.post("/api/v1/auth/login", json={"email": email, "password": new_password})
        out["login_new_password"] = r5.status_code
        data5 = r5.json()
        access4 = data5.get("access_token")
        hdr4 = {"Authorization": f"Bearer {access4}"} if access4 else {}

        out["logout_all"] = (await client.post("/api/v1/auth/logout", headers=hdr4, json={"all_sessions": True})).status_code if access4 else None

        print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(run())
