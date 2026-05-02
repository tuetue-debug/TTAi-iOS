<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { logout } from '../lib/auth'
import { getPortalOverview } from '../lib/portalData'
import { portalSections } from '../lib/portalSections'
import tuetueLogo from '../assets/Tuetue-ai-2m.jpg'

const route = useRoute()
const router = useRouter()
const loading = ref(true)
const error = ref('')
const overview = ref(null)
const sidebarCollapsed = ref(false)
const mobileMenuOpen = ref(false)
const theme = ref(getInitialTheme())

function getInitialTheme() {
  const stored = localStorage.getItem('tuetue-theme')
  if (stored) return stored
  if (window.matchMedia('(prefers-color-scheme: dark)').matches) return 'dark'
  return 'light'
}

function applyTheme(val) {
  document.documentElement.className = val === 'dark' ? 'theme-dark' : ''
  document.querySelector('meta[name=theme-color]').content = val === 'dark' ? '#0f172a' : '#f6f7fb'
  theme.value = val
  localStorage.setItem('tuetue-theme', val)
}

function toggleTheme() {
  applyTheme(theme.value === 'dark' ? 'light' : 'dark')
}

const navItems = [
  { to: '/dashboard', label: 'Overview', icon: '◫' },
  { to: '/dashboard/api-keys', label: 'API Keys', icon: '⟡' },
  { to: '/dashboard/usage', label: 'Usage', icon: '◔' },
  { to: '/dashboard/billing', label: 'Billing', icon: '◌' },
  { to: '/dashboard/limits', label: 'Limits', icon: '△' },
  { to: '/dashboard/docs', label: 'Docs', icon: '☰' },
  { to: '/dashboard/integrations', label: 'Integrations', icon: '✦' },
  { to: '/dashboard/profile', label: 'Profile', icon: '◉' },
]

const sectionKey = computed(() => {
  const parts = route.path.replace(/^\/dashboard\/?/, '')
  return parts || 'overview'
})

const sectionMeta = computed(() => portalSections[sectionKey.value] || portalSections.overview)

function isNavActive(item) {
  if (item.to === '/dashboard') return route.path === '/dashboard'
  return route.path === item.to
}

onMounted(async () => {
  applyTheme(theme.value)
  try {
    overview.value = await getPortalOverview()
  } catch (err) {
    await router.replace('/login')
    return
  } finally {
    loading.value = false
  }
})

watch(() => route.path, () => {
  mobileMenuOpen.value = false
})

function toggleSidebar() {
  sidebarCollapsed.value = !sidebarCollapsed.value
}

function closeMobileMenu() {
  mobileMenuOpen.value = false
}

async function handleLogout() {
  try { await logout() } catch (err) { error.value = err?.message || 'Logout failed' }
  await router.replace('/')
}
</script>

<template>
  <!-- Mobile overlay -->
  <div class="mobile-sidebar-overlay" :class="{ open: mobileMenuOpen }" @click="closeMobileMenu"></div>

  <!-- Mobile sidebar drawer -->
  <aside class="mobile-sidebar" :class="{ open: mobileMenuOpen }">
    <div class="mobile-sidebar-header">
      <div class="sidebar-brand">
        <img :src="tuetueLogo" alt="Tuệ Tuệ" class="brand-logo-image" />
        <div>
          <div class="brand-name">{{ $t('PortalLayout.ttaiPlatform_1') }}</div>
          <div class="brand-subtitle">console.tuetue.vn</div>
        </div>
      </div>
      <button class="mobile-sidebar-close" type="button" @click="closeMobileMenu" aria-label="Close menu">✕</button>
    </div>
    <nav>
      <RouterLink
        v-for="item in navItems"
        :key="item.to"
        :to="item.to"
        class="mobile-nav-link"
        :class="{ active: isNavActive(item) }"
      >
        <span class="nav-icon">{{ item.icon }}</span>
        <span>{{ item.label }}</span>
      </RouterLink>
    </nav>
  </aside>

  <div class="dashboard-shell mobile-hide-sidebar" :class="{ 'sidebar-collapsed': sidebarCollapsed }">
    <!-- Desktop sidebar -->
    <aside class="sidebar">
      <div class="sidebar-brand-row">
        <div v-if="!sidebarCollapsed" class="sidebar-brand">
          <img :src="tuetueLogo" alt="Tuệ Tuệ" class="brand-logo-image" />
          <div>
            <div class="brand-name">{{ $t('PortalLayout.ttaiPlatform_1') }}</div>
            <div class="brand-subtitle">console.tuetue.vn</div>
          </div>
        </div>
        <button class="sidebar-toggle" type="button" @click="toggleSidebar" :aria-pressed="sidebarCollapsed">
          ⋮
        </button>
      </div>
      <nav class="sidebar-nav">
        <RouterLink
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          class="nav-link"
          :class="{ active: isNavActive(item) }"
        >
          <span class="nav-icon">{{ item.icon }}</span>
          <span v-if="!sidebarCollapsed" class="nav-label">{{ item.label }}</span>
        </RouterLink>
      </nav>
    </aside>

    <section class="dashboard-main-shell">
      <header class="dashboard-topbar">
        <div>
          <button class="mobile-hamburger-btn" type="button" @click="mobileMenuOpen = true" aria-label="Open menu">☰</button>
          <div class="eyebrow">{{ sectionMeta.eyebrow }}</div>
          <h1 class="dashboard-title">{{ sectionMeta.title }}</h1>
          <p class="dashboard-subtitle">{{ sectionMeta.description }}</p>
        </div>
        <div class="dashboard-actions">
          <button class="theme-toggle-btn" @click="toggleTheme" :aria-label="theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'">
            {{ theme === 'dark' ? '☀' : '☾' }}
          </button>
          <button class="ghost-btn top-icon-btn" @click="router.push('/dashboard')" aria-label="Go to overview">⌂</button>
          <button class="ghost-btn top-action-btn" @click="router.push('/dashboard/docs')">{{ $t('PortalLayout.docs') }}</button>
          <button class="ghost-btn top-action-btn" @click="handleLogout">{{ $t('PortalLayout.logOut') }}</button>
        </div>
      </header>

      <main class="dashboard-main">
        <div v-if="loading" class="panel-card">
          <h3>Loading your workspace…</h3>
          <p>{{ $t('PortalLayout.checkingPortalSessionAndRestoring') }}</p>
        </div>

        <template v-else>
          <p v-if="error" class="form-error dashboard-error">{{ error }}</p>
          <router-view :overview="overview" />
        </template>
      </main>
    </section>
  </div>
</template>
