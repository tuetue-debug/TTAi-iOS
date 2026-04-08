import sys
import json
import os

sys.path.insert(0, r"C:\Users\vannt-pc\.openclaw\workspace\repos\TTAi-deployment\fastapi")
import user_auth  # noqa: E402


def with_env(env_updates, fn):
    old = {k: os.environ.get(k) for k in env_updates.keys()}
    try:
        for k, v in env_updates.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        return fn()
    finally:
        for k, v in old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def run():
    out = {}

    out["dev_seed_in_dev"] = with_env(
        {"ENVIRONMENT": "development", "TTAI_AUTH_SEED_TEST_USER": "1"},
        user_auth.should_seed_dev_user,
    )
    out["dev_seed_in_prod"] = with_env(
        {"ENVIRONMENT": "production", "TTAI_AUTH_SEED_TEST_USER": "1"},
        user_auth.should_seed_dev_user,
    )
    out["token_expose_default_dev"] = with_env(
        {"ENVIRONMENT": "development", "TTAI_AUTH_EXPOSE_FLOW_TOKENS": None},
        user_auth.should_expose_auth_tokens_in_response,
    )
    out["token_expose_default_prod"] = with_env(
        {"ENVIRONMENT": "production", "TTAI_AUTH_EXPOSE_FLOW_TOKENS": None},
        user_auth.should_expose_auth_tokens_in_response,
    )
    out["token_expose_override_prod"] = with_env(
        {"ENVIRONMENT": "production", "TTAI_AUTH_EXPOSE_FLOW_TOKENS": "true"},
        user_auth.should_expose_auth_tokens_in_response,
    )

    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    run()
