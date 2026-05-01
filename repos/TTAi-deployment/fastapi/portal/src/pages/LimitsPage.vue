<template>
  <section class="single-column-grid">
    <article class="panel-card">
      <h3>{{ $t('LimitsPage.limitsQuota') }}</h3>
      <p>{{ $t('LimitsPage.currentQuotaStateForThe') }}</p>
      <div class="detail-grid">
        <div class="detail-item">
          <span>{{ $t('LimitsPage.blockedEvents') }}</span>
          <strong>{{ overview?.limits?.quota_status?.blocked_events || 0 }}</strong>
        </div>
        <div class="detail-item">
          <span>{{ $t('LimitsPage.topReason') }}</span>
          <strong>{{ overview?.limits?.quota_status?.top_reason || '—' }}</strong>
        </div>
        <div class="detail-item">
          <span>{{ $t('LimitsPage.scopeType') }}</span>
          <strong>{{ overview?.limits?.scope?.type || 'user' }}</strong>
        </div>
        <div class="detail-item">
          <span>{{ $t('LimitsPage.scopeValue') }}</span>
          <strong>{{ overview?.limits?.scope?.value || overview?.user?.id || '—' }}</strong>
        </div>
      </div>
    </article>
  </section>
</template>

<script setup>
defineProps({ overview: { type: Object, required: true } })
</script>
