"""Payment routes — PayPal + Stripe checkout for TTAi subscriptions."""
from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx
from fastapi import APIRouter, Cookie, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from billing_store import load_billing_config
from payment_store import (
    complete_payment,
    create_invoice,
    create_payment,
    get_invoice,
    get_payment_by_order_id,
    get_user_subscription,
    list_invoices,
    list_payments,
    update_invoice_buyer_info,
    update_invoice_viettel,
    update_user_subscription,
)
from user_auth import USER_REPOSITORY, verify_token
import viettel_invoice as vi

PORTAL_SESSION_COOKIE = "ttai_portal_session"


def _resolve_portal_user(portal_session: str | None = Cookie(default=None, alias=PORTAL_SESSION_COOKIE)) -> dict:
    if not portal_session:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = verify_token(portal_session)
        user = USER_REPOSITORY.get_user_by_id(str(payload.get("sub")))
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid session") from exc
    if not user or not user.get("is_active"):
        raise HTTPException(status_code=401, detail="Invalid user")
    return user

logger = logging.getLogger(__name__)
router = APIRouter()

# ── Config ────────────────────────────────────────────────────────────────────

PAYPAL_CLIENT_ID = os.environ.get("PAYPAL_CLIENT_ID", "")
PAYPAL_SECRET = os.environ.get("PAYPAL_SECRET", "")
PAYPAL_MODE = os.environ.get("PAYPAL_MODE", "sandbox")
PAYPAL_BASE = "https://api-m.sandbox.paypal.com" if PAYPAL_MODE == "sandbox" else "https://api-m.paypal.com"

STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_PUBLISHABLE_KEY = os.environ.get("STRIPE_PUBLISHABLE_KEY", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")

CONSOLE_BASE_URL = os.environ.get("CONSOLE_BASE_URL", "https://console.tuetue.vn")


# ── PayPal helpers ────────────────────────────────────────────────────────────

async def _paypal_access_token() -> str:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{PAYPAL_BASE}/v1/oauth2/token",
            data={"grant_type": "client_credentials"},
            auth=(PAYPAL_CLIENT_ID, PAYPAL_SECRET),
            headers={"Accept": "application/json"},
            timeout=15,
        )
    if resp.status_code != 200:
        logger.error("PayPal token error: %s", resp.text)
        raise HTTPException(502, "PayPal authentication failed")
    return resp.json()["access_token"]


async def _paypal_create_order(amount_usd: float, plan: str, cycle: str) -> dict:
    token = await _paypal_access_token()
    payload = {
        "intent": "CAPTURE",
        "purchase_units": [{
            "amount": {"currency_code": "USD", "value": f"{amount_usd:.2f}"},
            "description": f"TTAi {plan.capitalize()} Plan ({cycle})",
        }],
        "application_context": {
            "brand_name": "TTAi Platform",
            "landing_page": "BILLING",
            "user_action": "PAY_NOW",
            "return_url": f"{CONSOLE_BASE_URL}/#/dashboard/billing?paypal=success",
            "cancel_url": f"{CONSOLE_BASE_URL}/#/dashboard/billing?paypal=cancel",
        },
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{PAYPAL_BASE}/v2/checkout/orders",
            json=payload,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            timeout=15,
        )
    if resp.status_code not in (200, 201):
        logger.error("PayPal create order error: %s", resp.text)
        raise HTTPException(502, "Could not create PayPal order")
    return resp.json()


async def _paypal_capture_order(order_id: str) -> dict:
    token = await _paypal_access_token()
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{PAYPAL_BASE}/v2/checkout/orders/{order_id}/capture",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            timeout=15,
        )
    if resp.status_code not in (200, 201):
        logger.error("PayPal capture error: %s", resp.text)
        raise HTTPException(502, "PayPal capture failed")
    return resp.json()


def _plan_price(plan: str, cycle: str) -> float:
    config = load_billing_config()
    plans = config.get("plans", {})
    p = plans.get(plan)
    if not p:
        raise HTTPException(400, f"Unknown plan: {plan}")
    if cycle == "yearly":
        return float(p["price_yearly_usd"])
    return float(p["price_monthly_usd"])


def _subscription_expires(cycle: str) -> str:
    now = datetime.now(timezone.utc)
    delta = timedelta(days=365) if cycle == "yearly" else timedelta(days=31)
    return (now + delta).isoformat()


# ── Request models ────────────────────────────────────────────────────────────

class CheckoutRequest(BaseModel):
    plan: str
    cycle: str = "monthly"


class CaptureRequest(BaseModel):
    order_id: str
    payment_id: str


# ── Plan endpoints ────────────────────────────────────────────────────────────

@router.get("/portal-api/billing/config")
async def get_payment_config():
    return {
        "stripe_publishable_key": STRIPE_PUBLISHABLE_KEY,
        "paypal_mode": PAYPAL_MODE,
        "stripe_enabled": bool(STRIPE_SECRET_KEY),
        "paypal_enabled": bool(PAYPAL_CLIENT_ID),
    }


@router.get("/portal-api/billing/plans")
async def get_plans():
    config = load_billing_config()
    return {"plans": config.get("plans", {})}


@router.get("/portal-api/billing/subscription")
async def get_subscription(user=Depends(_resolve_portal_user)):
    sub = get_user_subscription(str(user["id"]))
    config = load_billing_config()
    plan_detail = config.get("plans", {}).get(sub["tier"], {})
    return {"subscription": {**sub, "plan_detail": plan_detail}}


@router.get("/portal-api/billing/invoices")
async def get_invoices(user=Depends(_resolve_portal_user)):
    invoices = list_invoices(str(user["id"]))
    return {"invoices": invoices}


@router.get("/portal-api/billing/payments")
async def get_payments(user=Depends(_resolve_portal_user)):
    payments = list_payments(str(user["id"]))
    return {"payments": payments}


# ── PayPal checkout ───────────────────────────────────────────────────────────

@router.post("/portal-api/billing/checkout/paypal")
async def paypal_checkout(body: CheckoutRequest, user=Depends(_resolve_portal_user)):
    if body.plan == "free":
        raise HTTPException(400, "Cannot checkout free plan")
    if body.cycle not in ("monthly", "yearly"):
        raise HTTPException(400, "cycle must be monthly or yearly")

    amount = _plan_price(body.plan, body.cycle)
    order = await _paypal_create_order(amount, body.plan, body.cycle)
    order_id = order["id"]

    payment_id = create_payment(
        user_id=str(user["id"]),
        provider="paypal",
        plan=body.plan,
        billing_cycle=body.cycle,
        amount_usd=amount,
        provider_order_id=order_id,
    )

    approve_url = next(
        (link["href"] for link in order.get("links", []) if link["rel"] == "approve"),
        None,
    )
    return {"order_id": order_id, "payment_id": payment_id, "approve_url": approve_url}


@router.post("/portal-api/billing/checkout/paypal/capture")
async def paypal_capture(body: CaptureRequest, user=Depends(_resolve_portal_user)):
    capture = await _paypal_capture_order(body.order_id)
    status = capture.get("status")
    if status != "COMPLETED":
        raise HTTPException(402, f"Payment not completed: {status}")

    capture_id = capture["purchase_units"][0]["payments"]["captures"][0]["id"]

    payment = get_payment_by_order_id(body.order_id)
    if not payment or str(payment["user_id"]) != str(user["id"]):
        raise HTTPException(404, "Payment not found")

    complete_payment(payment["id"], body.order_id, capture_id)

    expires_at = _subscription_expires(payment["billing_cycle"])
    update_user_subscription(
        user_id=str(user["id"]),
        tier=payment["plan"],
        status="active",
        expires_at=expires_at,
    )

    now = datetime.now(timezone.utc)
    cycle = payment["billing_cycle"]
    period_end = (now + (timedelta(days=365) if cycle == "yearly" else timedelta(days=31))).isoformat()
    invoice_id = create_invoice(
        user_id=str(user["id"]),
        payment_id=payment["id"],
        plan=payment["plan"],
        billing_cycle=cycle,
        amount_usd=payment["amount_usd"],
        period_start=now.isoformat(),
        period_end=period_end,
    )

    return {
        "ok": True,
        "plan": payment["plan"],
        "expires_at": expires_at,
        "invoice_id": invoice_id,
    }


# ── Stripe checkout (skeleton — cần STRIPE_SECRET_KEY) ───────────────────────

@router.post("/portal-api/billing/checkout/stripe")
async def stripe_checkout(body: CheckoutRequest, user=Depends(_resolve_portal_user)):
    if not STRIPE_SECRET_KEY:
        raise HTTPException(503, "Stripe not configured")
    if body.plan == "free":
        raise HTTPException(400, "Cannot checkout free plan")
    if body.cycle not in ("monthly", "yearly"):
        raise HTTPException(400, "cycle must be monthly or yearly")

    amount_usd = _plan_price(body.plan, body.cycle)
    amount_cents = int(amount_usd * 100)

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.stripe.com/v1/checkout/sessions",
            auth=(STRIPE_SECRET_KEY, ""),
            data={
                "mode": "payment",
                "line_items[0][price_data][currency]": "usd",
                "line_items[0][price_data][unit_amount]": str(amount_cents),
                "line_items[0][price_data][product_data][name]": f"TTAi {body.plan.capitalize()} ({body.cycle})",
                "line_items[0][quantity]": "1",
                "success_url": f"{CONSOLE_BASE_URL}/#/dashboard/billing?stripe=success&session_id={{CHECKOUT_SESSION_ID}}",
                "cancel_url": f"{CONSOLE_BASE_URL}/#/dashboard/billing?stripe=cancel",
                "metadata[user_id]": str(user["id"]),
                "metadata[plan]": body.plan,
                "metadata[cycle]": body.cycle,
                "metadata[payment_id]": create_payment(
                    user_id=str(user["id"]),
                    provider="stripe",
                    plan=body.plan,
                    billing_cycle=body.cycle,
                    amount_usd=amount_usd,
                ),
            },
            timeout=15,
        )

    if resp.status_code != 200:
        logger.error("Stripe session error: %s", resp.text)
        raise HTTPException(502, "Could not create Stripe session")

    data = resp.json()
    return {"session_id": data["id"], "checkout_url": data["url"]}


@router.post("/portal-api/billing/webhook/stripe")
async def stripe_webhook(request: Request):
    """Stripe webhook — xác nhận payment và update subscription."""
    if not STRIPE_WEBHOOK_SECRET:
        raise HTTPException(503, "Stripe webhook not configured")

    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")

    # Verify Stripe signature
    import hashlib
    import hmac as hmac_lib
    import time
    try:
        parts = {}
        for item in sig.split(","):
            k, v = item.split("=", 1)
            parts[k] = v
        ts = parts.get("t", "0")
        v1 = parts.get("v1", "")
        signed_payload = f"{ts}.{payload.decode()}"
        expected = hmac_lib.new(
            STRIPE_WEBHOOK_SECRET.encode(),
            signed_payload.encode(),
            hashlib.sha256,
        ).hexdigest()
        if not hmac_lib.compare_digest(expected, v1):
            raise HTTPException(400, "Invalid signature")
        if abs(time.time() - int(ts)) > 300:
            raise HTTPException(400, "Webhook timestamp too old")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, f"Signature error: {e}")

    import json
    event = json.loads(payload)
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        meta = session.get("metadata", {})
        user_id = meta.get("user_id")
        plan = meta.get("plan")
        cycle = meta.get("cycle", "monthly")
        payment_id = meta.get("payment_id")

        if user_id and plan and payment_id:
            complete_payment(payment_id, session["id"], session.get("payment_intent", ""))
            expires_at = _subscription_expires(cycle)
            update_user_subscription(user_id, plan, "active", expires_at)
            now = datetime.now(timezone.utc)
            period_end = (now + (timedelta(days=365) if cycle == "yearly" else timedelta(days=31))).isoformat()
            amount_usd = session["amount_total"] / 100
            create_invoice(user_id, payment_id, plan, cycle, amount_usd, now.isoformat(), period_end)

    return {"received": True}


# ── Downgrade to free ─────────────────────────────────────────────────────────

@router.post("/portal-api/billing/cancel")
async def cancel_subscription(user=Depends(_resolve_portal_user)):
    update_user_subscription(str(user["id"]), "free", "active", None)
    return {"ok": True, "plan": "free"}


# ── Viettel S-Invoice (hoá đơn GTGT) ─────────────────────────────────────────

class VatInvoiceRequest(BaseModel):
    buyer_name: str = ""
    buyer_tax_code: str = ""
    buyer_address: str = ""


@router.post("/portal-api/billing/invoice/{invoice_id}/request-vat")
async def request_vat_invoice(
    invoice_id: str,
    body: VatInvoiceRequest,
    user=Depends(_resolve_portal_user),
):
    """User yêu cầu xuất hoá đơn GTGT cho invoice đã thanh toán."""
    inv = get_invoice(invoice_id)
    if not inv or inv["user_id"] != str(user["id"]):
        raise HTTPException(404, "Invoice not found")
    if inv.get("viettel_status") == "issued":
        return {"ok": True, "already_issued": True, "invoice_no": inv.get("viettel_invoice_no")}

    # Save buyer info
    update_invoice_buyer_info(
        invoice_id, body.buyer_name, body.buyer_tax_code, body.buyer_address
    )

    billing_config = load_billing_config()
    plan_info = billing_config.get("plans", {}).get(inv["plan"], {})
    item_name = f"Gói {plan_info.get('name', inv['plan'])} TTAi - {inv['billing_cycle']}"

    try:
        result = await vi.create_viettel_invoice(
            invoice_id=invoice_id,
            buyer_name=body.buyer_name or user.get("full_name", "Khách lẻ"),
            buyer_email=user.get("email", ""),
            buyer_tax_code=body.buyer_tax_code,
            buyer_address=body.buyer_address,
            item_name=item_name,
            amount_usd=inv["amount_usd"],
        )
    except RuntimeError as e:
        raise HTTPException(502, f"Viettel error: {e}")

    update_invoice_viettel(
        invoice_id,
        result["viettel_invoice_id"],
        result["viettel_invoice_no"],
        result["viettel_transaction_id"],
        viettel_status="issued",
    )
    return {
        "ok": True,
        "invoice_no": result["viettel_invoice_no"],
        "message": f"Hoá đơn số {result['viettel_invoice_no']} đã được phát hành.",
    }


@router.get("/portal-api/billing/invoice/{invoice_id}/vat-pdf")
async def download_vat_pdf(invoice_id: str, user=Depends(_resolve_portal_user)):
    """Download PDF hoá đơn GTGT từ Viettel."""
    from fastapi.responses import Response

    inv = get_invoice(invoice_id)
    if not inv or inv["user_id"] != str(user["id"]):
        raise HTTPException(404, "Invoice not found")
    if inv.get("viettel_status") != "issued" or not inv.get("viettel_invoice_id"):
        raise HTTPException(404, "VAT invoice not issued yet")

    try:
        pdf_bytes = await vi.get_invoice_pdf(
            inv["viettel_invoice_id"], inv["viettel_transaction_id"]
        )
    except RuntimeError as e:
        raise HTTPException(502, f"Viettel PDF error: {e}")

    filename = f"hoadon-{inv.get('viettel_invoice_no', invoice_id)}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
