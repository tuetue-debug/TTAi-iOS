<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import ChatLayout from '../components/ChatLayout.vue'
import { getCurrentUser, logout } from '../lib/auth'
import { getMemory, updateMemory, clearMemory } from '../lib/chatApi'

const router = useRouter()
const user = ref(null)
const facts = ref({})
const loading = ref(true)
const saving = ref(false)
const success = ref('')
const error = ref('')

onMounted(async () => {
  try { user.value = await getCurrentUser() } catch { router.push('/login'); return }
  await reload()
})

async function reload() {
  loading.value = true
  try {
    const res = await getMemory()
    facts.value = res.facts || {}
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

async function save() {
  saving.value = true
  error.value = ''
  try {
    await updateMemory(facts.value)
    success.value = 'Memory saved!'
    setTimeout(() => { success.value = '' }, 2500)
  } catch (e) {
    error.value = e.message
  } finally {
    saving.value = false
  }
}

async function handleClear() {
  if (!confirm('Clear all memory? This cannot be undone.')) return
  await clearMemory()
  facts.value = {}
  success.value = 'Memory cleared.'
  setTimeout(() => { success.value = '' }, 2500)
}

async function handleLogout() {
  await logout().catch(() => {})
  router.push('/login')
}

function factValue(val) {
  if (Array.isArray(val)) return val.join(', ')
  return String(val ?? '')
}

function updateFact(key, rawVal) {
  // If original was array, keep as array
  const orig = facts.value[key]
  if (Array.isArray(orig)) {
    facts.value[key] = rawVal.split(',').map(s => s.trim()).filter(Boolean)
  } else {
    facts.value[key] = rawVal
  }
}

const FIELD_LABELS = {
  name: 'Name',
  occupation: 'Occupation',
  location: 'Location',
  projects: 'Projects',
  tech_stack: 'Tech stack',
  preferences: 'Preferences',
  goals: 'Goals',
  other: 'Other facts',
}
</script>

<template>
  <ChatLayout :user="user" @logout="handleLogout">
    <div class="page-shell">
      <div class="page-inner">
        <h1 class="page-title">🧠 Memory</h1>
        <p style="color: var(--muted); font-size: 13px; margin-bottom: 20px;">
          TTAi remembers these facts about you across conversations.
          Facts are extracted automatically and you can edit them anytime.
        </p>

        <div v-if="loading" style="color: var(--muted);">Loading…</div>
        <template v-else>
          <p v-if="error" style="color: #ef4444; font-size: 13px; margin-bottom: 10px;">{{ error }}</p>
          <p v-if="success" style="color: #22c55e; font-size: 13px; margin-bottom: 10px;">{{ success }}</p>

          <div class="panel-card" v-if="Object.keys(facts).length">
            <div v-for="(val, key) in facts" :key="key" class="fact-item">
              <span class="fact-key">{{ FIELD_LABELS[key] || key }}</span>
              <div class="fact-val" style="flex: 1;">
                <input
                  class="form-input"
                  style="width: 100%;"
                  :value="factValue(val)"
                  @change="updateFact(key, $event.target.value)"
                />
              </div>
            </div>
          </div>
          <div v-else class="panel-card" style="color: var(--muted); font-size: 13px;">
            No memory yet. Start chatting and TTAi will learn about you automatically.
          </div>

          <div style="display: flex; gap: 10px; margin-top: 12px;">
            <button class="btn btn-primary" @click="save" :disabled="saving">
              {{ saving ? 'Saving…' : 'Save changes' }}
            </button>
            <button class="btn btn-danger" @click="handleClear">Clear all memory</button>
          </div>
        </template>
      </div>
    </div>
  </ChatLayout>
</template>
