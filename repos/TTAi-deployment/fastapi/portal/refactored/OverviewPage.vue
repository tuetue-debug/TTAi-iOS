<script setup>
import PortalPageIntro from '../components/PortalPageIntro.vue'
import PortalQuickActions from '../components/PortalQuickActions.vue'

defineProps({
  overview: { type: Object, required: true },
})
</script>

<template>
  <div class="overview-page">
    <PortalPageIntro
      eyebrow="LIVE ACCOUNT SNAPSHOT"
      title="Everything important, in one glance"
      description="A compact view of spend, request volume, key inventory, and quota pressure for your current account."
    />
    <PortalQuickActions />
    <section class="stats-grid overview-stats-grid">
      <article class="stat-card strong overview-stat-card">
        <div class="preview-label">Estimated spend</div>
        <div class="preview-metric">${{ Number(overview?.billing?.summary?.estimated_cost_total || 0).toFixed(6) }}</div>
        <p>Billable events: {{ overview?.billing?.summary?.billable_events || 0 }}</p>
      </article>
      <article class="stat-card overview-stat-card">
        <div class="preview-label">API keys</div>
        <div class="stat-number">{{ overview?.api_keys?.count || 0 }}</div>
        <p>Scoped keys with revoke and last-used tracking.</p>
      </article>
      <article class="stat-card overview-stat-card">
        <div class="preview-label">Requests (matched window)</div>
        <div class="stat-number">{{ overview?.usage?.summary?.total_requests || 0 }}</div>
        <p>Quota blocked: {{ overview?.limits?.quota_status?.blocked_events || 0 }}</p>
      </article>
    </section>

    <section class="dashboard-grid overview-grid">
      <article class="panel-card overview-panel-card overview-quickstart-card">
        <h3>Quick start</h3>
        <p>Generate your first key and test the chat endpoint in minutes.</p>
        <div class="overview-code-shell">
          <code>curl -H "Authorization: Bearer ttai_..." https://api.tuetue.vn/chat</code>
        </div>
      </article>
      <article class="panel-card overview-panel-card overview-direction-card">
        <h3>Portal direction</h3>
        <p>This console is now backed by real account, billing, usage, quota, and API key data.</p>
        <div class="mini-bars">
          <span style="height: 35%"></span>
          <span style="height: 58%"></span>
          <span style="height: 72%"></span>
          <span style="height: 48%"></span>
          <span style="height: 82%"></span>
          <span style="height: 64%"></span>
        </div>
      </article>
    </section>
  </div>
</template>
