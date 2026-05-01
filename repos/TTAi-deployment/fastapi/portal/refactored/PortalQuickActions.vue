<template>
  <section class="quick-actions-row">
    <RouterLink class="quick-action-card" to="/dashboard/api-keys">
      <span class="quick-action-kicker">Manage access</span>
      <strong>Open API keys</strong>
    </RouterLink>
    <RouterLink class="quick-action-card" to="/dashboard/docs">
      <span class="quick-action-kicker">Read integration guide</span>
      <strong>Open docs</strong>
    </RouterLink>
    <RouterLink class="quick-action-card" to="/dashboard/profile">
      <span class="quick-action-kicker">Account settings</span>
      <strong>Open profile</strong>
    </RouterLink>
  </section>
</template>
