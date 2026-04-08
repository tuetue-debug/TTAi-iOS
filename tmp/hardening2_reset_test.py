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
        email = f"reset_flow_{uuid.uuid4().hex[:8]}@example.com"
        password = "ResetOld123!"
        new_password = "ResetNew456!"
        out = {}

        reg = await client.post("/api/v1/auth/register", json={
            "name": "Reset Flow User",
            "email": email,
            "password": password,
        })
        out["register"] = reg.status_code

        forgot = await client.post("/api/v1/auth/forgot-password", json={
            "email": email,
        })
        out["forgot_password"] = forgot.status_code
        forgot_body = forgot.json()
        out["forgot_issued"] = forgot_body.get("issued")
        reset_token = forgot_body.get("reset_token")
        out["forgot_has_token"] = bool(reset_token)

        reset = await client.post("/api/v1/auth/reset-password", json={
            "token": reset_token,
            "new_password": new_password,
        })
        out["reset_password"] = reset.status_code

        login_old = await client.post("/api/v1/auth/login", json={
            "email": email,
            "password": password,
        })
        out["login_old_password_after_reset"] = login_old.status_code

        login_new = await client.post("/api/v1/auth/login", json={
            "email": email,
            "password": new_password,
        })
        out["login_new_password_after_reset"] = login_new.status_code

        reuse = await client.post("/api/v1/auth/reset-password", json={
            "token": reset_token,
            "new_password": "Another789!",
        })
        out["reuse_reset_token"] = reuse.status_code

        print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(run())
