<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import AuthCard from '../components/AuthCard.vue'
import { getCurrentUser } from '../lib/auth'
import tuetueLogo from '../assets/Tuetue-ai-2m.jpg'
import { useTheme } from '../composables/useTheme'

const router = useRouter()
const { theme, toggleTheme } = useTheme()

onMounted(async () => {
  try {
    await getCurrentUser()
    await router.replace('/dashboard')
  } catch {
    // stay on login page
  }
})
</script>

<template>
  <div class="auth-page-shell">
    <div class="auth-page-card">
      <div class="auth-page-copy">
        <img :src="tuetueLogo" alt="Tuệ Tuệ" class="auth-logo-image" />
        <RouterLink class="back-link" to="/">← Back to home</RouterLink>
        <span class="eyebrow">{{ $t('LoginPage.signIn') }}</span>
        <h1 class="auth-page-title">{{ $t('LoginPage.accessYourApiConsole') }}</h1>
        <p>
          Sign in to manage keys, inspect usage, track billing, and continue building with TTAi.
        </p>
      </div>
      <div style="position: relative;">
        <button class="theme-toggle-btn" @click="toggleTheme" style="position: absolute; top: 0; right: 0;" aria-label="Toggle theme">{{ theme === 'dark' ? '☀' : '☾' }}</button>
        <AuthCard mode="login" />
      </div>
    </div>
  </div>
</template>
