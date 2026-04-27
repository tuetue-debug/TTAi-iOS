<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { login } from '../lib/auth'
import { useTheme } from '../composables/useTheme'

const { toggleTheme, theme } = useTheme()
const router = useRouter()

const email = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

async function handleLogin() {
  error.value = ''
  loading.value = true
  try {
    await login(email.value, password.value)
    router.push('/c/new')
  } catch (e) {
    error.value = e.message || 'Login failed'
  } finally {
    loading.value = false
  }
}

function continueAsGuest() {
  router.push('/c/new')
}
</script>

<template>
  <div class="auth-shell">
    <div class="auth-card">
      <div style="display:flex; justify-content: space-between; align-items: flex-start;">
        <div>
          <div style="display:flex; align-items:center; gap:10px; margin-bottom:4px;">
            <img :src="'/chat/logo.jpg'" alt="Tuệ Tuệ Ai" style="width:40px;height:40px;object-fit:contain;border-radius:8px;" />
            <div>
              <div class="auth-logo" style="margin-bottom:0;">Tuệ Tuệ Ai</div>
              <div style="font-size:11px;color:var(--muted);letter-spacing:0.04em;">intelligence.</div>
            </div>
          </div>
          <div class="auth-subtitle">Sign in to save conversations and unlock memory</div>
        </div>
        <button @click="toggleTheme" style="background:none;border:none;cursor:pointer;font-size:18px; color:var(--muted);">
          {{ theme === 'dark' ? '☀️' : '🌙' }}
        </button>
      </div>

      <form @submit.prevent="handleLogin">
        <div class="auth-field">
          <label class="auth-label">Email</label>
          <input
            class="auth-input"
            type="email"
            v-model="email"
            placeholder="you@example.com"
            required
            autocomplete="email"
          />
        </div>
        <div class="auth-field">
          <label class="auth-label">Password</label>
          <input
            class="auth-input"
            type="password"
            v-model="password"
            placeholder="••••••••"
            required
            autocomplete="current-password"
          />
        </div>
        <p v-if="error" class="auth-error">{{ error }}</p>
        <button class="auth-btn" type="submit" :disabled="loading">
          {{ loading ? 'Signing in…' : 'Sign in' }}
        </button>
      </form>

      <div style="margin-top: 12px; text-align: center;">
        <button
          @click="continueAsGuest"
          style="background:none;border:none;cursor:pointer;color:var(--muted);font-size:13px;text-decoration:underline;"
        >Continue as guest (10 free messages)</button>
      </div>

      <div class="auth-links">
        Don't have an account?
        <a href="https://console.tuetue.vn/signup" target="_blank">Create one at Console ↗</a>
      </div>
      <div class="auth-links" style="margin-top: 8px;">
        <a href="https://console.tuetue.vn/dashboard/billing" target="_blank">Upgrade plan ↗</a>
      </div>
    </div>
  </div>
</template>
