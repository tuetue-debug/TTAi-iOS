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
        email = f"verify_flow_{uuid.uuid4().hex[:8]}@example.com"
        password = "VerifyPass123!"
        out = {}

        reg = await client.post("/api/v1/auth/register", json={
            "name": "Verify Flow User",
            "email": email,
            "password": password,
        })
        out["register"] = reg.status_code
        reg_body = reg.json()
        access = reg_body.get("access_token")
        out["initial_email_verified"] = (reg_body.get("user") or {}).get("email_verified")
        hdr = {"Authorization": f"Bearer {access}"}

        req = await client.post("/api/v1/auth/verify-email/request", headers=hdr)
        out["verify_request"] = req.status_code
        req_body = req.json()
        token = req_body.get("verification_token")
        out["verify_request_has_token"] = bool(token)

        verify = await client.post("/api/v1/auth/verify-email", json={"token": token})
        out["verify_email"] = verify.status_code
        verify_body = verify.json()
        out["verified_user_email_verified"] = ((verify_body.get("user") or {}).get("email_verified") if isinstance(verify_body.get("user"), dict) else None)

        me = await client.get("/api/v1/auth/me", headers=hdr)
        out["me_after_verify"] = me.status_code
        me_body = me.json()
        out["me_email_verified"] = me_body.get("email_verified")

        reuse = await client.post("/api/v1/auth/verify-email", json={"token": token})
        out["reuse_verify_token"] = reuse.status_code

        print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(run())
