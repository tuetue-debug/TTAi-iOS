<template>
  <section class="quick-actions-row">
    <RouterLink class="quick-action-card" to="/dashboard/api-keys">
      <span class="quick-action-kicker">{{ $t('PortalQuickActions.manageAccess') }}</span>
      <strong>{{ $t('PortalQuickActions.openApiKeys') }}</strong>
    </RouterLink>
    <RouterLink class="quick-action-card" to="/dashboard/docs">
      <span class="quick-action-kicker">{{ $t('PortalQuickActions.readIntegrationGuide') }}</span>
      <strong>{{ $t('PortalQuickActions.openDocs') }}</strong>
    </RouterLink>
    <RouterLink class="quick-action-card" to="/dashboard/profile">
      <span class="quick-action-kicker">{{ $t('PortalQuickActions.accountSettings') }}</span>
      <strong>{{ $t('PortalQuickActions.openProfile') }}</strong>
    </RouterLink>
  </section>
</template>
