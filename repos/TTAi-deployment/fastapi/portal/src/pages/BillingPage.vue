<script setup>
import { onMounted, ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import {
  getBillingPaymentConfig,
  getBillingPlans,
  getBillingSubscription,
  getBillingInvoices,
  checkoutPaypal,
  capturePaypal,
  checkoutStripe,
  cancelSubscription,
  requestVatInvoice,
  downloadVatPdf,
} from '../lib/portalData'

defineProps({ overview: { type: Object, default: null } })

const route = useRoute()
const loading = ref(true)
const actionLoading = ref(false)
const error = ref('')
const success = ref('')
const plans = ref({})
const subscription = ref(null)
const invoices = ref([])
const selectedCycle = ref('monthly')
const paymentConfig = ref({ stripe_enabled: false, paypal_enabled: false })

onMounted(async () => {
  try {
    const [cfgRes, plansRes, subRes, invRes] = await Promise.all([
      getBillingPaymentConfig(),
      getBillingPlans(),
      getBillingSubscription(),
      getBillingInvoices(),
    ])
    paymentConfig.value = cfgRes
    plans.value = plansRes.plans || {}
    subscription.value = subRes.subscription || null
    invoices.value = invRes.invoices || []
  } catch (err) {
    error.value = err?.message || 'Failed to load billing info'
  } finally {
    loading.value = false
  }

  // Handle PayPal return
  const paypalStatus = route.query.paypal
  const orderId = route.query.token
  const paymentId = sessionStorage.getItem('ttai_paypal_payment_id')
  if (paypalStatus === 'success' && orderId && paymentId) {
    sessionStorage.removeItem('ttai_paypal_payment_id')
    await handlePaypalCapture(orderId, paymentId)
  } else if (paypalStatus === 'cancel') {
    error.value = 'PayPal payment was cancelled.'
  }

  // Handle Stripe return
  if (route.query.stripe === 'success') {
    success.value = 'Payment successful! Your subscription has been updated.'
    await reloadSubscription()
  } else if (route.query.stripe === 'cancel') {
    error.value = 'Stripe payment was cancelled.'
  }
})

async function reloadSubscription() {
  try {
    const subRes = await getBillingSubscription()
    subscription.value = subRes.subscription || null
    const invRes = await getBillingInvoices()
    invoices.value = invRes.invoices || []
  } catch {}
}

async function handlePaypalCapture(orderId, paymentId) {
  actionLoading.value = true
  error.value = ''
  try {
    const res = await capturePaypal(orderId, paymentId)
    success.value = `Upgraded to ${res.plan} plan! Invoice: ${res.invoice_id}`
    await reloadSubscription()
  } catch (err) {
    error.value = err?.message || 'Payment capture failed'
  } finally {
    actionLoading.value = false
  }
}

async function handlePaypal(planKey) {
  actionLoading.value = true
  error.value = ''
  success.value = ''
  try {
    const res = await checkoutPaypal(planKey, selectedCycle.value)
    sessionStorage.setItem('ttai_paypal_payment_id', res.payment_id)
    window.location.href = res.approve_url
  } catch (err) {
    error.value = err?.message || 'PayPal checkout failed'
    actionLoading.value = false
  }
}

async function handleStripe(planKey) {
  actionLoading.value = true
  error.value = ''
  success.value = ''
  try {
    const res = await checkoutStripe(planKey, selectedCycle.value)
    window.location.href = res.checkout_url
  } catch (err) {
    error.value = err?.message || 'Stripe checkout failed'
    actionLoading.value = false
  }
}

async function handleCancel() {
  if (!confirm('Downgrade to Free plan?')) return
  actionLoading.value = true
  error.value = ''
  try {
    await cancelSubscription()
    success.value = 'Subscription cancelled. Downgraded to Free plan.'
    await reloadSubscription()
  } catch (err) {
    error.value = err?.message || 'Cancel failed'
  } finally {
    actionLoading.value = false
  }
}

const currentTier = computed(() => subscription.value?.tier || 'free')
const planList = computed(() => Object.entries(plans.value).map(([key, val]) => ({ key, ...val })))
const yearlyDiscount = (plan) => {
  if (!plan.price_monthly_usd) return null
  const saved = plan.price_monthly_usd * 12 - plan.price_yearly_usd
  return saved > 0 ? Math.round((saved / (plan.price_monthly_usd * 12)) * 100) : null
}

// VAT invoice
const vatModal = ref(null)   // invoice being requested
const vatForm = ref({ buyer_name: '', buyer_tax_code: '', buyer_address: '' })
const vatLoading = ref(false)

function openVatModal(inv) {
  vatModal.value = inv
  vatForm.value = {
    buyer_name: inv.buyer_name || '',
    buyer_tax_code: inv.buyer_tax_code || '',
    buyer_address: inv.buyer_address || '',
  }
}

async function submitVatRequest() {
  if (!vatModal.value) return
  vatLoading.value = true
  error.value = ''
  try {
    const res = await requestVatInvoice(vatModal.value.id, vatForm.value)
    success.value = res.message || 'Hoá đơn GTGT đã được phát hành!'
    vatModal.value = null
    await reloadSubscription()
  } catch (err) {
    error.value = err?.message || 'Lỗi xuất hoá đơn'
  } finally {
    vatLoading.value = false
  }
}

async function handleDownloadPdf(inv) {
  try {
    const blob = await downloadVatPdf(inv.id)
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `hoadon-${inv.viettel_invoice_no || inv.id}.pdf`
    a.click()
    URL.revokeObjectURL(url)
  } catch (err) {
    error.value = err?.message || 'Không tải được PDF'
  }
}
</script>

<template>
  <section class="single-column-grid">

    <!-- Usage summary -->
    <article class="panel-card" v-if="overview">
      <h3 style="margin-top:0">{{ $t('BillingPage.usageThisMonth') }}</h3>
      <div class="detail-grid">
        <div class="detail-item">
          <span>{{ $t('BillingPage.estimatedCost') }}</span>
          <strong>${{ Number(overview?.billing?.summary?.estimated_cost_total || 0).toFixed(4) }}</strong>
        </div>
        <div class="detail-item">
          <span>{{ $t('BillingPage.billableEvents') }}</span>
          <strong>{{ overview?.billing?.summary?.billable_events || 0 }}</strong>
        </div>
        <div class="detail-item">
          <span>{{ $t('BillingPage.topProvider') }}</span>
          <strong>{{ overview?.billing?.summary?.top_provider || '—' }}</strong>
        </div>
        <div class="detail-item">
          <span>{{ $t('BillingPage.topModel') }}</span>
          <strong>{{ overview?.billing?.summary?.top_model || '—' }}</strong>
        </div>
      </div>
    </article>

    <!-- Loading -->
    <div v-if="loading" class="empty-state">Loading billing info…</div>

    <template v-else>
      <!-- Alerts -->
      <p v-if="error" class="form-error">{{ error }}</p>
      <p v-if="success" class="form-success">{{ success }}</p>

      <!-- Current subscription -->
      <article class="panel-card" v-if="subscription">
        <h3 style="margin-top:0">{{ $t('BillingPage.currentPlan_1') }}</h3>
        <div class="detail-grid">
          <div class="detail-item">
            <span>{{ $t('BillingPage.plan') }}</span>
            <strong style="text-transform:capitalize">{{ subscription.tier }}</strong>
          </div>
          <div class="detail-item">
            <span>{{ $t('BillingPage.status') }}</span>
            <strong>{{ subscription.status }}</strong>
          </div>
          <div class="detail-item">
            <span>{{ $t('BillingPage.expires') }}</span>
            <strong>{{ subscription.expires_at ? new Date(subscription.expires_at).toLocaleDateString() : 'Never (Free)' }}</strong>
          </div>
          <div class="detail-item">
            <span>{{ $t('BillingPage.requestsMonth') }}</span>
            <strong>{{ subscription.plan_detail?.quota?.max_requests?.toLocaleString() || '—' }}</strong>
          </div>
        </div>
        <button
          v-if="subscription.tier !== 'free'"
          class="ghost-btn"
          style="margin-top:12px; color:#ef4444"
          :disabled="actionLoading"
          @click="handleCancel"
        >{{ $t('BillingPage.downgradeToFree') }}</button>
      </article>

      <!-- Plan selection -->
      <article class="panel-card">
        <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:16px">
          <h3 style="margin:0">{{ $t('BillingPage.upgradePlan') }}</h3>
          <div class="cycle-toggle">
            <button
              :class="['ghost-btn', selectedCycle === 'monthly' ? 'active-cycle' : '']"
              @click="selectedCycle = 'monthly'"
            >{{ $t('BillingPage.monthly') }}</button>
            <button
              :class="['ghost-btn', selectedCycle === 'yearly' ? 'active-cycle' : '']"
              @click="selectedCycle = 'yearly'"
            >{{ $t('BillingPage.yearly') }} <span style="color:#22c55e; font-size:12px">Save up to 20%</span></button>
          </div>
        </div>

        <div class="plan-grid">
          <div
            v-for="plan in planList"
            :key="plan.key"
            :class="['plan-card', plan.key === currentTier ? 'plan-card--current' : '']"
          >
            <div class="plan-header">
              <span class="plan-name">{{ plan.name }}</span>
              <span v-if="plan.key === currentTier" class="plan-badge">{{ $t('BillingPage.current') }}</span>
              <span v-if="yearlyDiscount(plan) && selectedCycle === 'yearly'" class="plan-discount">
                -{{ yearlyDiscount(plan) }}%
              </span>
            </div>

            <div class="plan-price">
              <template v-if="selectedCycle === 'monthly'">
                <span class="plan-amount">${{ plan.price_monthly_usd }}</span>
                <span class="plan-period">/month</span>
              </template>
              <template v-else>
                <span class="plan-amount">${{ plan.price_yearly_usd }}</span>
                <span class="plan-period">/year</span>
              </template>
            </div>

            <ul class="plan-features">
              <li v-for="f in plan.features" :key="f">{{ f }}</li>
            </ul>

            <div class="plan-actions" v-if="plan.key !== 'free' && plan.key !== currentTier">
              <button
                class="primary-btn full"
                :disabled="actionLoading"
                @click="handlePaypal(plan.key)"
              >
                {{ actionLoading ? 'Processing…' : 'Pay with PayPal' }}
              </button>
              <button
                class="ghost-btn full"
                style="margin-top:8px"
                :disabled="actionLoading || !paymentConfig.stripe_enabled"
                :title="!paymentConfig.stripe_enabled ? 'Stripe not configured' : ''"
                @click="handleStripe(plan.key)"
              >
                Pay with Card (Stripe)
              </button>
            </div>
            <div v-else-if="plan.key === 'free' && currentTier === 'free'" class="plan-actions">
              <button class="ghost-btn full" disabled>Current plan</button>
            </div>
          </div>
        </div>
      </article>

      <!-- Invoice history -->
      <article class="panel-card" v-if="invoices.length">
        <h3 style="margin-top:0">Lịch sử thanh toán</h3>
        <div class="key-list">
          <div v-for="inv in invoices" :key="inv.id" class="key-item invoice-row">
            <div style="flex:1; min-width:0">
              <div class="key-name">{{ inv.id }}</div>
              <div class="key-meta">
                {{ inv.plan }} · {{ inv.billing_cycle }} ·
                {{ new Date(inv.created_at).toLocaleDateString('vi-VN') }}
              </div>
              <div v-if="inv.viettel_status === 'issued'" class="vat-badge issued">
                Hoá đơn GTGT: {{ inv.viettel_invoice_no }}
              </div>
            </div>
            <div style="display:flex; align-items:center; gap:8px; flex-shrink:0">
              <strong>${{ Number(inv.amount_usd).toFixed(2) }}</strong>
              <button
                v-if="inv.viettel_status !== 'issued'"
                class="ghost-btn vat-btn"
                @click="openVatModal(inv)"
              >Xuất HĐ GTGT</button>
              <button
                v-else
                class="ghost-btn vat-btn"
                @click="handleDownloadPdf(inv)"
              >Tải PDF</button>
            </div>
          </div>
        </div>
      </article>
      <article class="panel-card" v-else>
        <h3 style="margin-top:0">Lịch sử thanh toán</h3>
        <div class="empty-state">Chưa có hoá đơn nào.</div>
      </article>

      <!-- VAT Invoice Modal -->
      <div v-if="vatModal" class="modal-backdrop" @click.self="vatModal = null">
        <div class="modal-card">
          <h3 style="margin-top:0">Yêu cầu hoá đơn GTGT</h3>
          <p style="color:#64748b; font-size:13px; margin-top:-4px">
            Invoice {{ vatModal.id }} · ${{ Number(vatModal.amount_usd).toFixed(2) }}
          </p>
          <div class="form-group">
            <label>Tên doanh nghiệp / cá nhân</label>
            <input v-model="vatForm.buyer_name" placeholder="Công ty TNHH ..." class="form-input" />
          </div>
          <div class="form-group">
            <label>Mã số thuế (để trống nếu cá nhân)</label>
            <input v-model="vatForm.buyer_tax_code" placeholder="0123456789" class="form-input" />
          </div>
          <div class="form-group">
            <label>Địa chỉ</label>
            <input v-model="vatForm.buyer_address" placeholder="123 Nguyễn Văn A, TP.HCM" class="form-input" />
          </div>
          <p v-if="error" class="form-error">{{ error }}</p>
          <div style="display:flex; gap:8px; margin-top:16px">
            <button class="primary-btn" :disabled="vatLoading" @click="submitVatRequest">
              {{ vatLoading ? 'Đang xử lý…' : 'Phát hành hoá đơn' }}
            </button>
            <button class="ghost-btn" @click="vatModal = null">Huỷ</button>
          </div>
        </div>
      </div>
    </template>

  </section>
</template>

<style scoped>
.cycle-toggle { display: flex; gap: 8px; }
.active-cycle { border-color: var(--accent, #6366f1); color: var(--accent, #6366f1); }

.plan-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}
.plan-card {
  border: 1px solid var(--border, #e2e8f0);
  border-radius: 10px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.plan-card--current {
  border-color: var(--accent, #6366f1);
  background: color-mix(in srgb, var(--accent, #6366f1) 5%, transparent);
}
.plan-header { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.plan-name { font-weight: 700; font-size: 16px; }
.plan-badge {
  font-size: 11px; padding: 2px 8px;
  background: var(--accent, #6366f1); color: #fff; border-radius: 99px;
}
.plan-discount {
  font-size: 11px; padding: 2px 8px;
  background: #22c55e; color: #fff; border-radius: 99px;
}
.plan-price { display: flex; align-items: baseline; gap: 4px; }
.plan-amount { font-size: 28px; font-weight: 800; }
.plan-period { color: #64748b; font-size: 13px; }
.plan-features { padding-left: 16px; margin: 0; color: #475569; font-size: 13px; display: flex; flex-direction: column; gap: 4px; }
.plan-actions { display: flex; flex-direction: column; margin-top: auto; }
.full { width: 100%; }

.invoice-row { align-items: flex-start; }
.vat-badge { font-size: 11px; margin-top: 4px; padding: 2px 8px; border-radius: 99px; display: inline-block; }
.vat-badge.issued { background: #dcfce7; color: #16a34a; }
.vat-btn { font-size: 12px; padding: 4px 10px; white-space: nowrap; }

.modal-backdrop {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.4);
  display: flex; align-items: center; justify-content: center;
  z-index: 1000;
}
.modal-card {
  background: var(--surface, #fff);
  border-radius: 12px;
  padding: 24px;
  width: 100%; max-width: 440px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.2);
}
.form-group { display: flex; flex-direction: column; gap: 4px; margin-bottom: 12px; }
.form-group label { font-size: 13px; font-weight: 500; color: #475569; }
.form-input {
  padding: 8px 12px; border-radius: 8px;
  border: 1px solid var(--border, #e2e8f0);
  background: var(--bg, #f8fafc);
  font-size: 14px; color: inherit;
}
.form-input:focus { outline: none; border-color: var(--accent, #6366f1); }
</style>
