"""
viettel_invoice.py — Viettel S-Invoice (hoá đơn điện tử GTGT)

Calls go through VIETTEL_PROXY_URL (matbao.vn static IP) to satisfy
Viettel's IP whitelist requirement. TTAi server has dynamic DDNS IP.

Env vars:
  VIETTEL_USERNAME      — tài khoản S-Invoice
  VIETTEL_PASSWORD      — mật khẩu
  VIETTEL_TAX_CODE      — MST bên bán (TTAi)
  VIETTEL_TEMPLATE_CODE — mẫu số (e.g. "1/001")
  VIETTEL_SERIES        — ký hiệu (e.g. "AA/26E")
  VIETTEL_PROXY_URL     — https://sinvoice.tuetue.vn/sinvoice-proxy.php
                          (để trống = gọi thẳng Viettel, cần IP tĩnh)
  VIETTEL_SANDBOX       — "1" để dùng môi trường demo
  VIETTEL_VND_RATE      — tỷ giá USD→VND (default 25000)
  VIETTEL_TAX_RATE      — % thuế GTGT (default 10)
"""
from __future__ import annotations

import json
import logging
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────

VIETTEL_USERNAME      = os.environ.get("VIETTEL_USERNAME", "")
VIETTEL_PASSWORD      = os.environ.get("VIETTEL_PASSWORD", "")
VIETTEL_TAX_CODE      = os.environ.get("VIETTEL_TAX_CODE", "")
VIETTEL_TEMPLATE_CODE = os.environ.get("VIETTEL_TEMPLATE_CODE", "1/001")
VIETTEL_SERIES        = os.environ.get("VIETTEL_SERIES", "AA/26E")
VIETTEL_PROXY_URL     = os.environ.get("VIETTEL_PROXY_URL", "").rstrip("/")
VIETTEL_SANDBOX       = os.environ.get("VIETTEL_SANDBOX", "1") == "1"
VIETTEL_VND_RATE      = int(os.environ.get("VIETTEL_VND_RATE", "25000"))
VIETTEL_TAX_RATE      = int(os.environ.get("VIETTEL_TAX_RATE", "10"))

_DIRECT_BASE = (
    "https://api-demo.viettel.vn/services/einvoiceapplication/api"
    if VIETTEL_SANDBOX else
    "https://api-vinvoice.viettel.vn/services/einvoiceapplication/api"
)

def _base_url() -> str:
    """Return effective base URL — proxy nếu có, otherwise direct."""
    return VIETTEL_PROXY_URL if VIETTEL_PROXY_URL else _DIRECT_BASE


# ── Token cache ───────────────────────────────────────────────────────────────

_token_cache: dict = {"token": None, "expires_at": 0.0}

def _is_token_valid() -> bool:
    return bool(_token_cache["token"]) and time.time() < _token_cache["expires_at"] - 60

async def _login() -> str:
    if _is_token_valid():
        return _token_cache["token"]

    url = f"{_base_url()}/auth/login"
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(url, json={
            "username": VIETTEL_USERNAME,
            "password": VIETTEL_PASSWORD,
        })
        resp.raise_for_status()

    # Token comes back in Set-Cookie: access_token=<jwt>
    cookie = resp.cookies.get("access_token")
    if not cookie:
        # Some versions return in body
        body = resp.json()
        cookie = body.get("access_token") or body.get("token")
    if not cookie:
        raise RuntimeError("Viettel login: no access_token in response")

    _token_cache["token"] = cookie
    _token_cache["expires_at"] = time.time() + 8 * 3600  # 8h TTL
    logger.info("Viettel: token refreshed")
    return cookie


def _auth_headers(token: str) -> dict:
    return {
        "Cookie": f"access_token={token}",
        "Content-Type": "application/json",
    }


# ── Helpers ───────────────────────────────────────────────────────────────────

def usd_to_vnd(amount_usd: float) -> int:
    """Convert USD to VND, round to nearest 1000."""
    vnd = round(amount_usd * VIETTEL_VND_RATE / 1000) * 1000
    return max(vnd, 1000)


def _build_payload(
    invoice_id: str,
    buyer_name: str,
    buyer_email: str,
    buyer_tax_code: str,
    buyer_address: str,
    item_name: str,
    amount_usd: float,
) -> dict:
    amount_vnd = usd_to_vnd(amount_usd)
    tax_amount = round(amount_vnd * VIETTEL_TAX_RATE / 100)
    issued_ms  = int(datetime.now(timezone.utc).timestamp() * 1000)

    return {
        "generalInvoiceInfo": {
            "invoiceType":      "01GTKT",
            "templateCode":     VIETTEL_TEMPLATE_CODE,
            "invoiceSeries":    VIETTEL_SERIES,
            "currencyCode":     "VND",
            "exchangeRate":     1,
            "invoiceIssuedDate": issued_ms,
            "transactionUuid":  str(uuid.uuid4()),
            "paymentMethodName": "Chuyển khoản",
            "invoiceNote":      f"Ref: {invoice_id}",
        },
        "buyerInfo": {
            "buyerName":        buyer_name or "Khách lẻ",
            "buyerIdNo":        buyer_tax_code or "",
            "buyerEmail":       buyer_email,
            "buyerAddressLine": buyer_address or "",
        },
        "itemInfo": [{
            "lineNumber":                    1,
            "itemName":                      item_name,
            "unitName":                      "Gói",
            "quantity":                      1,
            "unitPrice":                     amount_vnd,
            "taxPercentage":                 VIETTEL_TAX_RATE,
            "itemTotalAmountWithoutTax":      amount_vnd,
            "itemTotalAmountWithTax":         amount_vnd + tax_amount,
            "taxAmount":                     tax_amount,
        }],
        "summarizeInfo": {
            "sumOfTotalLineAmountWithoutTax": amount_vnd,
            "totalAmountWithoutTax":          amount_vnd,
            "totalTaxAmount":                 tax_amount,
            "totalAmountWithTax":             amount_vnd + tax_amount,
            "totalAmountWithTaxInWords":      "",
        },
    }


# ── Public API ────────────────────────────────────────────────────────────────

async def create_viettel_invoice(
    invoice_id: str,
    buyer_name: str,
    buyer_email: str,
    buyer_tax_code: str,
    buyer_address: str,
    item_name: str,
    amount_usd: float,
) -> dict:
    """
    Tạo hoá đơn trên Viettel S-Invoice.
    Returns {"invoice_id": str, "invoice_no": str, "transaction_id": str}
    """
    if not VIETTEL_USERNAME or not VIETTEL_TAX_CODE:
        raise RuntimeError("Viettel S-Invoice chưa được cấu hình (VIETTEL_USERNAME, VIETTEL_TAX_CODE)")

    token = await _login()
    payload = _build_payload(
        invoice_id, buyer_name, buyer_email,
        buyer_tax_code, buyer_address, item_name, amount_usd,
    )

    url = f"{_base_url()}/InvoiceAPI/InvoiceWS/createInvoice/{VIETTEL_TAX_CODE}"
    async with httpx.AsyncClient(timeout=90) as client:
        resp = await client.post(url, json=payload, headers=_auth_headers(token))
        resp.raise_for_status()

    data = resp.json()
    if data.get("errorCode") not in (None, ""):
        raise RuntimeError(f"Viettel error {data.get('errorCode')}: {data.get('description')}")

    result = data.get("result") or {}
    logger.info("Viettel invoice created: %s", result.get("invoiceNo"))
    return {
        "viettel_invoice_id":  result.get("invoiceId", ""),
        "viettel_invoice_no":  result.get("invoiceNo", ""),
        "viettel_transaction_id": result.get("transactionId", ""),
    }


async def get_invoice_pdf(viettel_invoice_id: str, viettel_transaction_id: str) -> bytes:
    """Lấy PDF hoá đơn (base64 → bytes)."""
    token = await _login()
    payload = {
        "supplierTaxCode": VIETTEL_TAX_CODE,
        "templateCode":    VIETTEL_TEMPLATE_CODE,
        "invoiceSeries":   VIETTEL_SERIES,
        "fileType":        "PDF",
        "invoiceId":       viettel_invoice_id,
        "transactionId":   viettel_transaction_id,
    }
    url = f"{_base_url()}/InvoiceAPI/InvoiceUtilsWS/getInvoiceRepresentationFile"
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(url, json=payload, headers=_auth_headers(token))
        resp.raise_for_status()

    data = resp.json()
    if data.get("errorCode") not in (None, ""):
        raise RuntimeError(f"Viettel PDF error: {data.get('description')}")

    import base64
    file_data = data.get("fileToBytes") or data.get("result", {}).get("fileToBytes", "")
    return base64.b64decode(file_data)


async def cancel_invoice(viettel_transaction_id: str, reason: str = "Huỷ theo yêu cầu") -> bool:
    """Huỷ hoá đơn đã phát hành."""
    token = await _login()
    payload = {
        "supplierTaxCode":  VIETTEL_TAX_CODE,
        "transactionId":    viettel_transaction_id,
        "strIRSDate":       datetime.now(timezone.utc).strftime("%Y%m%d"),
        "additionalReferenceDesc": reason,
        "additionalReferenceDate": int(datetime.now(timezone.utc).timestamp() * 1000),
    }
    url = f"{_base_url()}/InvoiceAPI/InvoiceWS/cancelTransactionInvoice"
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(url, json=payload, headers=_auth_headers(token))
        resp.raise_for_status()

    data = resp.json()
    return data.get("errorCode") in (None, "")
