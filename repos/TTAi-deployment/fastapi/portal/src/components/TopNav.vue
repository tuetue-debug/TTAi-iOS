<template>
  <header class="topbar">
    <div class="brand-wrap">
      <img src="/assets/logo.jpg" alt="Tue Tue" class="brand-logo" />
      <div class="brand-text brand-text-mobile-hidden">
        <div class="brand-name">Tue Tue Console</div>
      </div>
    </div>
    <nav class="topnav desktop-only">
      <a href="#features">{{ $t('FeaturesPage.features') }}</a>
      <a href="#pricing">{{ $t('FeaturesPage.pricing_1') || 'Pricing' }}</a>
    </nav>
    <div class="top-actions">
      <button class="theme-toggle-btn top-icon-btn" @click="toggleTheme" :title="themeTitle" :aria-label="themeTitle">
        <span class="theme-icon" aria-hidden="true">{{ themeIcon }}</span>
      </button>
      <div class="locale-selector">
        <button class="locale-btn" @click="toggleLocaleMenu" title="Change language">
          <span class="locale-flag">{{ currentLocale.flag }}</span>
          <span class="locale-code">{{ currentLocale.code }}</span>
        </button>
        <div v-if="localeMenuOpen" class="locale-dropdown">
          <button v-for="loc in locales" :key="loc.value" class="locale-option" @click="switchLocale(loc.value)">
            <span class="locale-flag">{{ loc.flag }}</span>
            <span class="locale-code">{{ loc.code }}</span>
          </button>
        </div>
      </div>
      <RouterLink v-if="!isLoggedIn && !isAuthPage" class="primary-btn link-btn" to="/signup">{{ $t('LandingPage.signUpButton') || 'Start building' }}</RouterLink>
      <button class="mobile-menu-btn" @click="toggleMobileMenu" :aria-expanded="mobileMenuOpen ? 'true' : 'false'" aria-label="Open navigation menu">
        <span></span><span></span><span></span>
      </button>
    </div>
  </header>
  <div v-if="mobileMenuOpen" class="mobile-menu-dropdown">
    <a href="#features" @click="closeMobileMenu">{{ $t('FeaturesPage.features') }}</a>
    <a href="#pricing" @click="closeMobileMenu">{{ $t('FeaturesPage.pricing_1') || 'Pricing' }}</a>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { setLocale } from '../i18n/index.js'

const route = useRoute()
const isLoggedIn = ref(false) // TODO: connect to real auth state
const isAuthPage = computed(() => route.path === '/login' || route.path === '/signup')
const localeMenuOpen = ref(false)
const mobileMenuOpen = ref(false)
const theme = ref(document.documentElement.classList.contains('theme-dark') ? 'dark' : 'light')

const locales = [
  { value: 'en', flag: '🇺🇸', code: 'EN' },
  { value: 'vi', flag: '🇻🇳', code: 'VI' },
  { value: 'fr', flag: '🇫🇷', code: 'FR' },
  { value: 'zh', flag: '🇨🇳', code: 'ZH' },
  { value: 'ko', flag: '🇰🇷', code: 'KO' },
  { value: 'ja', flag: '🇯🇵', code: 'JA' },
]

const currentLocale = computed(() => {
  const saved = localStorage.getItem('tuetue-locale') || 'en'
  return locales.find(l => l.value === saved) || locales[0]
})

function toggleLocaleMenu() {
  localeMenuOpen.value = !localeMenuOpen.value
  mobileMenuOpen.value = false
}

function toggleMobileMenu() {
  mobileMenuOpen.value = !mobileMenuOpen.value
  localeMenuOpen.value = false
}

function closeMobileMenu() {
  mobileMenuOpen.value = false
}

async function switchLocale(value) {
  localStorage.setItem('tuetue-locale', value)
  localeMenuOpen.value = false
  await setLocale(value)
}

function toggleTheme() {
  const next = theme.value === 'dark' ? 'light' : 'dark'
  document.documentElement.className = 'theme-' + next
  localStorage.setItem('tuetue-theme', next)
  theme.value = next
}

const themeTitle = computed(() => {
  return theme.value === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'
})

const themeIcon = computed(() => {
  return theme.value === 'dark' ? '☀' : '☾'
})
</script>
