import sys
import json
import asyncio
import uuid
import os
import httpx

sys.path.insert(0, r"C:\Users\vannt-pc\.openclaw\workspace\repos\TTAi-deployment\fastapi")
import main  # noqa: E402


async def run_case(env_value: str, jwt_secret: str | None = None):
    old_env = os.environ.get("ENVIRONMENT")
    old_secret = os.environ.get("TTAI_JWT_SECRET")
    os.environ["ENVIRONMENT"] = env_value
    if jwt_secret is None:
        os.environ.pop("TTAI_JWT_SECRET", None)
    else:
        os.environ["TTAI_JWT_SECRET"] = jwt_secret

    try:
        transport = httpx.ASGITransport(app=main.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            email = f"bridge_{env_value}_{uuid.uuid4().hex[:6]}@example.com"
            password = "BridgePass123!"
            out = {"env": env_value}

            reg = await client.post("/api/v1/auth/register", json={
                "name": "Bridge User",
                "email": email,
                "password": password,
            })
            out["register"] = reg.status_code
            reg_body = reg.json()
            access = reg_body.get("access_token")
            out["register_has_access"] = bool(access)

            forgot = await client.post("/api/v1/auth/forgot-password", json={"email": email})
            forgot_body = forgot.json()
            out["forgot_status"] = forgot.status_code
            out["forgot_delivery_mode"] = forgot_body.get("delivery_mode")
            out["forgot_delivery_status"] = forgot_body.get("delivery_status")
            out["forgot_has_token"] = "reset_token" in forgot_body

            if access:
                hdr = {"Authorization": f"Bearer {access}"}
                verify_req = await client.post("/api/v1/auth/verify-email/request", headers=hdr)
                verify_body = verify_req.json()
                out["verify_status"] = verify_req.status_code
                out["verify_delivery_mode"] = verify_body.get("delivery_mode")
                out["verify_delivery_status"] = verify_body.get("delivery_status")
                out["verify_has_token"] = "verification_token" in verify_body
            else:
                out["verify_status"] = None

            return out
    finally:
        if old_env is None:
            os.environ.pop("ENVIRONMENT", None)
        else:
            os.environ["ENVIRONMENT"] = old_env
        if old_secret is None:
            os.environ.pop("TTAI_JWT_SECRET", None)
        else:
            os.environ["TTAI_JWT_SECRET"] = old_secret


async def main_async():
    dev_case = await run_case("development")
    prod_case = await run_case("production", jwt_secret="prod-secret-for-test")
    print(json.dumps({"dev": dev_case, "prod": prod_case}, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main_async())
