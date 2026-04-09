<script setup>
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { logout } from '../lib/auth'
import { getPortalOverview } from '../lib/portalData'
import { portalSections } from '../lib/portalSections'

const route = useRoute()
const router = useRouter()
const loading = ref(true)
const error = ref('')
const overview = ref(null)

const sectionKey = computed(() => {
  const parts = route.path.replace(/^\/dashboard\/?/, '')
  return parts || 'overview'
})

const sectionMeta = computed(() => portalSections[sectionKey.value] || portalSections.overview)

onMounted(async () => {
  try {
    overview.value = await getPortalOverview()
  } catch (err) {
    await router.replace('/login')
    return
  } finally {
    loading.value = false
  }
})

async function handleLogout() {
  try {
    await logout()
  } catch (err) {
    error.value = err?.message || 'Logout failed'
  } finally {
    await router.replace('/login')
  }
}
</script>

<template>
  <div class="dashboard-shell">
    <aside class="sidebar">
      <div class="sidebar-brand">
        <div class="brand-mark">T</div>
        <div>
          <div class="brand-name">TTAi Platform</div>
          <div class="brand-subtitle">console.tuetue.vn</div>
        </div>
      </div>

      <nav class="sidebar-nav">
        <RouterLink to="/dashboard" active-class="active">Overview</RouterLink>
        <RouterLink to="/dashboard/api-keys" active-class="active">API Keys</RouterLink>
        <RouterLink to="/dashboard/usage" active-class="active">Usage</RouterLink>
        <RouterLink to="/dashboard/billing" active-class="active">Billing</RouterLink>
        <RouterLink to="/dashboard/limits" active-class="active">Limits</RouterLink>
        <RouterLink to="/dashboard/docs" active-class="active">Docs</RouterLink>
        <RouterLink to="/dashboard/profile" active-class="active">Profile</RouterLink>
      </nav>
    </aside>

    <main class="dashboard-main">
      <div v-if="loading" class="panel-card">
        <h3>Loading your workspace…</h3>
        <p>Checking portal session and restoring your console.</p>
      </div>

      <template v-else>
        <header class="dashboard-topbar">
          <div>
            <div class="eyebrow">{{ sectionMeta.eyebrow }}</div>
            <h1 class="dashboard-title">{{ sectionMeta.title }}</h1>
            <p class="dashboard-subtitle">{{ sectionMeta.description }}</p>
          </div>
          <div class="dashboard-actions">
            <div class="user-badge">
              <span class="user-badge-label">Signed in as</span>
              <strong>{{ overview?.user?.email || overview?.user?.name || 'builder' }}</strong>
            </div>
            <button class="ghost-btn" @click="router.push('/dashboard/docs')">Docs</button>
            <button class="ghost-btn" @click="handleLogout">Log out</button>
          </div>
        </header>

        <p v-if="error" class="form-error dashboard-error">{{ error }}</p>

        <router-view :overview="overview" />
      </template>
    </main>
  </div>
</template>
