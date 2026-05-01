<template>
  <section class="single-column-grid">
    <article class="panel-card">
      <h3>{{ $t('UsagePage.usageSummary') }}</h3>
      <p>{{ $t('UsagePage.matchedRequestsAndUsageSignals') }}</p>
      <div class="detail-grid">
        <div class="detail-item">
          <span>{{ $t('UsagePage.totalRequests') }}</span>
          <strong>{{ overview?.usage?.summary?.total_requests || 0 }}</strong>
        </div>
        <div class="detail-item">
          <span>{{ $t('UsagePage.successfulRequests') }}</span>
          <strong>{{ overview?.usage?.summary?.success_count || 0 }}</strong>
        </div>
        <div class="detail-item">
          <span>{{ $t('UsagePage.errorRequests') }}</span>
          <strong>{{ overview?.usage?.summary?.error_count || 0 }}</strong>
        </div>
        <div class="detail-item">
          <span>{{ $t('UsagePage.totalTokensEst') }}</span>
          <strong>{{ overview?.usage?.summary?.total_tokens_est || 0 }}</strong>
        </div>
      </div>
    </article>
  </section>
</template>

<script setup>
defineProps({ overview: { type: Object, required: true } })
</script>
