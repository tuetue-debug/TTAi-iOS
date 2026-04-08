"""Auth delivery bridge helpers for forgot/reset and verify-email flows."""
from __future__ import annotations

import logging
from typing import Dict

from user_auth import should_expose_auth_tokens_in_response, get_runtime_environment

logger = logging.getLogger(__name__)


def get_auth_delivery_mode() -> str:
    return "inline_token" if should_expose_auth_tokens_in_response() else "delivery_pending"


def build_forgot_password_delivery_response(result: Dict) -> Dict:
    mode = get_auth_delivery_mode()
    response = {
        "message": "If the account exists, password reset instructions have been prepared.",
        "issued": result.get("issued", False),
        "delivery_mode": mode,
    }
    if result.get("issued") and mode == "inline_token":
        response["reset_token"] = result.get("reset_token")
        response["expires_in"] = result.get("expires_in")
        response["expires_at"] = result.get("expires_at")
    elif result.get("issued") and mode == "delivery_pending":
        response["delivery_status"] = "provider_not_configured"
        logger.info(
            "Auth delivery pending for forgot-password in environment=%s; no outbound provider configured yet.",
            get_runtime_environment(),
        )
    return response


def build_verify_email_delivery_response(result: Dict) -> Dict:
    mode = get_auth_delivery_mode()
    response = {
        "message": "Email verification instructions have been prepared.",
        "issued": result.get("issued", True),
        "delivery_mode": mode,
    }
    if mode == "inline_token":
        response["verification_token"] = result.get("verification_token")
        response["expires_in"] = result.get("expires_in")
        response["expires_at"] = result.get("expires_at")
    else:
        response["delivery_status"] = "provider_not_configured"
        logger.info(
            "Auth delivery pending for verify-email in environment=%s; no outbound provider configured yet.",
            get_runtime_environment(),
        )
    return response
