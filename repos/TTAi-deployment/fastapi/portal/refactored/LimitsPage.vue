<template>
  <section class="single-column-grid">
    <article class="panel-card">
      <h3>Limits & quota</h3>
      <p>Current quota state for the authenticated account.</p>
      <div class="detail-grid">
        <div class="detail-item">
          <span>Blocked events</span>
          <strong>{{ overview?.limits?.quota_status?.blocked_events || 0 }}</strong>
        </div>
        <div class="detail-item">
          <span>Top reason</span>
          <strong>{{ overview?.limits?.quota_status?.top_reason || '—' }}</strong>
        </div>
        <div class="detail-item">
          <span>Scope type</span>
          <strong>{{ overview?.limits?.scope?.type || 'user' }}</strong>
        </div>
        <div class="detail-item">
          <span>Scope value</span>
          <strong>{{ overview?.limits?.scope?.value || overview?.user?.id || '—' }}</strong>
        </div>
      </div>
    </article>
  </section>
</template>

<script setup>
defineProps({ overview: { type: Object, required: true } })
</script>
