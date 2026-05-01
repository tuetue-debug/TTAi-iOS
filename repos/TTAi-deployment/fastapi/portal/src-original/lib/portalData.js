import { portalFetch } from './auth'

export async function getPortalOverview() {
  return portalFetch('/portal-api/overview', { method: 'GET' })
}

export async function getPortalApiKeys() {
  return portalFetch('/portal-api/api-keys', { method: 'GET' })
}

export async function createPortalApiKey(form) {
  return portalFetch('/portal-api/api-keys', {
    method: 'POST',
    body: JSON.stringify(form),
  })
}

export async function revokePortalApiKey(keyId) {
  return portalFetch(`/portal-api/api-keys/${keyId}`, {
    method: 'DELETE',
  })
}

export async function getBillingPaymentConfig() {
  return portalFetch('/portal-api/billing/config', { method: 'GET' })
}

export async function getBillingPlans() {
  return portalFetch('/portal-api/billing/plans', { method: 'GET' })
}

export async function getBillingSubscription() {
  return portalFetch('/portal-api/billing/subscription', { method: 'GET' })
}

export async function getBillingInvoices() {
  return portalFetch('/portal-api/billing/invoices', { method: 'GET' })
}

export async function checkoutPaypal(plan, cycle) {
  return portalFetch('/portal-api/billing/checkout/paypal', {
    method: 'POST',
    body: JSON.stringify({ plan, cycle }),
  })
}

export async function capturePaypal(orderId, paymentId) {
  return portalFetch('/portal-api/billing/checkout/paypal/capture', {
    method: 'POST',
    body: JSON.stringify({ order_id: orderId, payment_id: paymentId }),
  })
}

export async function checkoutStripe(plan, cycle) {
  return portalFetch('/portal-api/billing/checkout/stripe', {
    method: 'POST',
    body: JSON.stringify({ plan, cycle }),
  })
}

export async function cancelSubscription() {
  return portalFetch('/portal-api/billing/cancel', { method: 'POST' })
}

export async function requestVatInvoice(invoiceId, buyerInfo) {
  return portalFetch(`/portal-api/billing/invoice/${invoiceId}/request-vat`, {
    method: 'POST',
    body: JSON.stringify(buyerInfo),
  })
}

export async function downloadVatPdf(invoiceId) {
  const res = await fetch(`/portal-api/billing/invoice/${invoiceId}/vat-pdf`, {
    credentials: 'include',
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Download failed' }))
    throw new Error(err.detail || 'Download failed')
  }
  return res.blob()
}
