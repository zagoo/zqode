"""Smoke test: boot the app against in-memory SQLite, exercise each module's golden path."""
import asyncio
import os
import sys
from datetime import datetime, timedelta, timezone

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("JWT_SECRET_KEY", "test_secret_change_me_long_enough_for_local_smoke_only")
os.environ.setdefault("INITIAL_ADMIN_ENTERPRISE_EMAIL", "admin@example.com")
os.environ.setdefault("ALLOWED_EMAIL_DOMAINS", "example.com")
os.environ.setdefault("EMAIL_MODE", "console")

from httpx import ASGITransport, AsyncClient  # noqa: E402

from app.core.bootstrap import run_bootstrap  # noqa: E402
from app.database import engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Base  # noqa: E402


async def _setup_schema() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def _login_admin(client: AsyncClient) -> tuple[str, str]:
    r = await client.post("/api/v1/auth/login/challenges", json={"enterprise_email": "admin@example.com"})
    assert r.status_code == 201, r.text
    challenge = r.json()["data"]
    password = challenge["dev_random_password"]
    r = await client.post(
        "/api/v1/auth/login/sessions",
        json={
            "challenge_id": challenge["challenge_id"],
            "enterprise_email": "admin@example.com",
            "random_password": password,
        },
    )
    assert r.status_code == 201, r.text
    session = r.json()["data"]
    return session["access_token"], session["refresh_token"]


async def main() -> int:
    await _setup_schema()
    await run_bootstrap()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        access, refresh = await _login_admin(client)
        h = {"Authorization": f"Bearer {access}"}
        print("[auth] login OK")

        # me
        r = await client.get("/api/v1/auth/me", headers=h)
        assert r.status_code == 200, r.text
        me = r.json()["data"]
        assert me["user"]["enterprise_email"] == "admin@example.com"
        print(f"[auth] /me OK — role={me['user']['role_name']} permissions={len(me['permissions'])}")

        # admin: create provider (mock://)
        r = await client.post(
            "/api/v1/admin/providers",
            headers=h,
            json={
                "provider_name": "MockOpenAI",
                "api_base_url": "mock://local",
                "api_key": "sk-fake-openai",
                "api_description": "smoke test",
            },
        )
        assert r.status_code == 201, r.text
        provider = r.json()["data"]
        print(f"[admin] provider created {provider['provider_id']} mask={provider['api_key_mask']}")

        # admin: create model
        r = await client.post(
            "/api/v1/admin/models",
            headers=h,
            json={
                "provider_id": provider["provider_id"],
                "model_name": "gpt-4o-mini",
                "input_price_per_million_tokens": "0.5",
                "output_price_per_million_tokens": "1.5",
                "currency": "USD",
            },
        )
        assert r.status_code == 201, r.text
        model = r.json()["data"]
        print(f"[admin] model created {model['model_id']}")

        # admin: create openapi endpoint
        r = await client.post(
            "/api/v1/admin/enterprise-openapis",
            headers=h,
            json={
                "api_name": "OpenAI Gateway",
                "api_type": "OPENAI_COMPATIBLE",
                "gateway_url": "https://gateway.example.com/openai/v1/chat/completions",
                "usage_description": "Use with OpenAI clients.",
            },
        )
        assert r.status_code == 201, r.text
        openapi = r.json()["data"]
        print(f"[admin] openapi created {openapi['openapi_id']}")

        # admin: list users (only admin so far)
        r = await client.get("/api/v1/admin/users", headers=h)
        assert r.status_code == 200, r.text
        users = r.json()["data"]
        assert users["total"] == 1
        print(f"[admin] users.total={users['total']}")

        # admin: list roles
        r = await client.get("/api/v1/admin/roles", headers=h)
        roles = r.json()["data"]["items"]
        assert {r["role_name"] for r in roles} == {"System Administrator", "Team Manager", "Normal User"}
        normal_role = next(r for r in roles if r["role_name"] == "Normal User")
        print(f"[admin] roles seeded ({len(roles)})")

        # admin: quota policy
        r = await client.get("/api/v1/admin/quota-reset-policy", headers=h)
        assert r.status_code == 200
        print(f"[admin] quota policy default reset_mode={r.json()['data']['reset_mode']}")

        # admin: create a normal user for the workbench/gateway flow
        r = await client.post(
            "/api/v1/admin/users",
            headers=h,
            json={
                "enterprise_email": "dev@example.com",
                "role_id": normal_role["role_id"],
                "cost_limit_source": "ROLE_DEFAULT",
                "account_status": "ENABLED",
            },
        )
        assert r.status_code == 201, r.text
        dev_user = r.json()["data"]

        # admin: extend api keys (no keys yet, just verify list)
        r = await client.get("/api/v1/admin/api-keys", headers=h)
        assert r.status_code == 200

        # log in as the dev user
        r = await client.post("/api/v1/auth/login/challenges", json={"enterprise_email": "dev@example.com"})
        challenge = r.json()["data"]
        r = await client.post(
            "/api/v1/auth/login/sessions",
            json={
                "challenge_id": challenge["challenge_id"],
                "enterprise_email": "dev@example.com",
                "random_password": challenge["dev_random_password"],
            },
        )
        assert r.status_code == 201, r.text
        dev_access = r.json()["data"]["access_token"]
        dev_h = {"Authorization": f"Bearer {dev_access}"}
        print("[auth] dev user logged in")

        # workbench: model & openapi catalog
        r = await client.get("/api/v1/workbench/models", headers=dev_h)
        assert r.status_code == 200 and r.json()["data"]["total"] == 1
        r = await client.get("/api/v1/workbench/enterprise-openapis", headers=dev_h)
        assert r.status_code == 200 and r.json()["data"]["total"] == 1
        print("[workbench] catalogs OK")

        # workbench: create API key
        expires = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
        r = await client.post(
            "/api/v1/workbench/api-keys", headers=dev_h, json={"key_name": "Smoke key", "expires_at": expires}
        )
        assert r.status_code == 201, r.text
        api_key_raw = r.json()["data"]["api_key_secret"]
        api_key_meta = r.json()["data"]["api_key"]
        assert api_key_raw.startswith("sk-")
        print(f"[workbench] api key created mask={api_key_meta['api_key_mask']}")

        # gateway: hit the OpenAI-compatible endpoint with the API key
        r = await client.post(
            f"/api/v1/gateway/{openapi['openapi_id']}/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key_raw}"},
            json={
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": "Hello, gateway."}],
            },
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["choices"][0]["message"]["content"].startswith("[mock gpt-4o-mini]")
        usage = body["usage"]
        assert usage["prompt_tokens"] > 0 and usage["completion_tokens"] > 0
        print(f"[gateway] request OK — usage={usage}")

        # analytics: personal consumption should now show one request
        r = await client.get("/api/v1/analytics/personal-consumption", headers=dev_h)
        assert r.status_code == 200, r.text
        personal = r.json()["data"]
        assert personal["total_tokens"] == usage["prompt_tokens"] + usage["completion_tokens"]
        print(
            f"[analytics] personal OK — tokens={personal['total_tokens']} cost={personal['total_cost']} ratio={personal['quota_usage_ratio']:.4f}"
        )

        # admin: details endpoint should see the request too
        r = await client.get("/api/v1/analytics/consumption-details", headers=h)
        assert r.status_code == 200
        details = r.json()["data"]
        assert details["total"] == 1
        print(f"[analytics] details OK — total={details['total']} status={details['items'][0]['status']}")

        # admin: summary
        r = await client.get("/api/v1/analytics/consumption-summary", headers=h)
        assert r.status_code == 200
        print(f"[analytics] summary OK — buckets={len(r.json()['data'])}")

        # refresh token round-trip
        r = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
        assert r.status_code == 200, r.text
        print("[auth] refresh OK")

        # negative: workbench create with expiry > role validity should fail
        too_long = (datetime.now(timezone.utc) + timedelta(days=10_000)).isoformat()
        r = await client.post(
            "/api/v1/workbench/api-keys", headers=dev_h, json={"key_name": "TooLong", "expires_at": too_long}
        )
        assert r.status_code == 422 and r.json()["data"]["error_code"] == "API_KEY_VALIDITY_EXCEEDED"
        print("[workbench] validity-cap check OK")

        # negative: bad API key on gateway
        r = await client.post(
            f"/api/v1/gateway/{openapi['openapi_id']}/v1/chat/completions",
            headers={"Authorization": "Bearer sk-not-real"},
            json={"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "x"}]},
        )
        assert r.status_code == 401 and r.json()["data"]["error_code"] == "API_KEY_INVALID"
        print("[gateway] bad key correctly rejected")

    print("\nALL SMOKE TESTS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
