import sys
import json
import asyncio
import uuid
import httpx

sys.path.insert(0, r"C:\Users\vannt-pc\.openclaw\workspace\repos\TTAi-deployment\fastapi")
import main  # noqa: E402


async def run():
    transport = httpx.ASGITransport(app=main.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        email = f"tighten_flow_{uuid.uuid4().hex[:8]}@example.com"
        password = "TightPass123!"
        out = {}

        reg = await client.post("/api/v1/auth/register", json={
            "name": "Tighten User",
            "email": email,
            "password": password,
        })
        out["register"] = reg.status_code
        reg_body = reg.json()
        access = reg_body.get("access_token")
        hdr = {"Authorization": f"Bearer {access}"}

        update = await client.put("/api/v1/auth/me", headers=hdr, json={"name": "Tighten User Updated"})
        out["auth_me_put"] = update.status_code
        update_body = update.json()
        out["auth_me_put_deprecated"] = update_body.get("deprecated")
        out["auth_me_put_replacement"] = update_body.get("replacement")

        cleanup = await client.post("/api/v1/auth/sessions/cleanup", headers=hdr)
        out["sessions_cleanup"] = cleanup.status_code
        cleanup_body = cleanup.json()
        out["sessions_cleanup_has_cleanup"] = isinstance(cleanup_body.get("cleanup"), dict)

        print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(run())
