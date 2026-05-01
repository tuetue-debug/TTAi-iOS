<template>
  <section class="single-column-grid">
    <article class="panel-card">
      <h3>Usage summary</h3>
      <p>Matched requests and usage signals from the truth layer.</p>
      <div class="detail-grid">
        <div class="detail-item">
          <span>Total requests</span>
          <strong>{{ overview?.usage?.summary?.total_requests || 0 }}</strong>
        </div>
        <div class="detail-item">
          <span>Successful requests</span>
          <strong>{{ overview?.usage?.summary?.success_count || 0 }}</strong>
        </div>
        <div class="detail-item">
          <span>Error requests</span>
          <strong>{{ overview?.usage?.summary?.error_count || 0 }}</strong>
        </div>
        <div class="detail-item">
          <span>Total tokens est.</span>
          <strong>{{ overview?.usage?.summary?.total_tokens_est || 0 }}</strong>
        </div>
      </div>
    </article>
  </section>
</template>

<script setup>
defineProps({ overview: { type: Object, required: true } })
</script>
