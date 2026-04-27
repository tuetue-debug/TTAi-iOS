<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { getConversations, deleteConversation } from '../lib/chatApi'

const props = defineProps({
  collapsed: Boolean,
  user: { type: Object, default: null },
  currentConvId: { type: String, default: null },
})
const emit = defineEmits(['new-chat', 'logout'])
const router = useRouter()

const conversations = ref([])

// ── System status ────────────────────────────────
const STATUS_COLOR = { green: '#22c55e', yellow: '#f59e0b', red: '#ef4444' }
const systemStatus = ref('yellow') // green / yellow / red
let statusTimer = null

async function checkStatus() {
  try {
    const res = await fetch('/control-api/public/rag/health', { signal: AbortSignal.timeout(5000) })
    if (!res.ok) { systemStatus.value = 'red'; return }
    const data = await res.json()
    const s = data.service_status || data.status || ''
    if (s === 'operational' || s === 'ok') systemStatus.value = 'green'
    else if (s === 'degraded') systemStatus.value = 'yellow'
    else systemStatus.value = 'red'
  } catch {
    systemStatus.value = 'red'
  }
}

onMounted(() => {
  loadConversations()
  checkStatus()
  statusTimer = setInterval(checkStatus, 30000)
})

onUnmounted(() => clearInterval(statusTimer))

async function loadConversations() {
  try {
    const res = await getConversations()
    conversations.value = res.conversations || []
  } catch {}
}

// Expose reload to parent via defineExpose
defineExpose({ loadConversations })

function groupByDate(convs) {
  const now = new Date()
  const today = now.toDateString()
  const yesterday = new Date(now - 86400000).toDateString()
  const weekAgo = new Date(now - 7 * 86400000)

  const groups = { Today: [], Yesterday: [], 'Last 7 days': [], Older: [] }
  for (const c of convs) {
    const d = new Date(c.updated_at)
    const ds = d.toDateString()
    if (ds === today) groups['Today'].push(c)
    else if (ds === yesterday) groups['Yesterday'].push(c)
    else if (d >= weekAgo) groups['Last 7 days'].push(c)
    else groups['Older'].push(c)
  }
  return groups
}

const grouped = computed(() => groupByDate(conversations.value))

async function handleDelete(e, convId) {
  e.stopPropagation()
  if (!confirm('Delete this conversation?')) return
  await deleteConversation(convId)
  conversations.value = conversations.value.filter(c => c.id !== convId)
  if (props.currentConvId === convId) router.push('/c/new')
}

function userInitials(user) {
  if (!user) return '?'
  const name = user.full_name || user.email || ''
  return name.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2) || '?'
}
</script>

<template>
  <aside>
    <!-- Header -->
    <div class="sidebar-header">
      <img :src="'/chat/logo.jpg'" alt="Tuệ Tuệ Ai" class="sidebar-logo-img" />
      <div v-if="!collapsed" class="sidebar-brand">
        <span class="sidebar-logo-name">Tuệ Tuệ Ai</span>
        <span class="sidebar-logo-sub">intelligence.</span>
      </div>
    </div>

    <!-- New chat -->
    <button class="new-chat-btn" @click="emit('new-chat')">
      <svg class="icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
        <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
      </svg>
      <span v-if="!collapsed">New chat</span>
    </button>

    <!-- Nav links (auth only) -->
    <template v-if="user && !collapsed">
      <div class="sidebar-section-label">Tools</div>
      <nav class="sidebar-nav">
        <router-link to="/memory" class="sidebar-nav-item" active-class="active">
          🧠 <span>Memory</span>
        </router-link>
        <router-link to="/projects" class="sidebar-nav-item" active-class="active">
          📁 <span>Projects</span>
        </router-link>
      </nav>
    </template>

    <!-- Conversation list -->
    <div class="conv-list" v-if="!collapsed">
      <template v-for="(convs, label) in grouped" :key="label">
        <template v-if="convs.length">
          <div class="conv-group-label">{{ label }}</div>
          <div
            v-for="conv in convs"
            :key="conv.id"
            class="conv-item"
            :class="{ active: conv.id === currentConvId }"
            @click="router.push(`/c/${conv.id}`)"
          >
            <span class="conv-title">{{ conv.title || 'New chat' }}</span>
            <button class="conv-delete" @click="handleDelete($event, conv.id)" title="Delete">✕</button>
          </div>
        </template>
      </template>
      <div v-if="!conversations.length" style="padding: 12px 8px; font-size: 12px; color: var(--sidebar-muted);">
        No conversations yet
      </div>
    </div>

    <!-- Footer -->
    <div class="sidebar-footer">
      <div class="user-row" v-if="user">
        <div class="user-avatar">{{ userInitials(user) }}</div>
        <div v-if="!collapsed" style="flex: 1; overflow: hidden;">
          <div style="font-size: 12px; color: var(--sidebar-text); overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
            {{ user.full_name || user.email }}
          </div>
          <div style="font-size: 10px; color: var(--sidebar-muted);">{{ user.subscription_tier || 'free' }}</div>
        </div>
      </div>
      <div class="user-row" v-else>
        <div class="user-avatar" style="background: #64748b;">?</div>
        <span v-if="!collapsed" style="font-size: 12px;">Guest</span>
      </div>

      <template v-if="!collapsed">
        <button v-if="user" class="goto-console" @click="emit('logout')">
          Sign out
        </button>
        <a v-else href="/login#" class="goto-console" @click.prevent="router.push('/login')" style="display:block;">
          Sign in for full access →
        </a>
        <a href="https://console.tuetue.vn/dashboard/billing" target="_blank" class="goto-console">
          Upgrade plan ↗
        </a>
      </template>

      <!-- Status + Version -->
      <div style="display:flex; align-items:center; gap:7px; padding: 8px 4px 2px;">
        <span
          :title="systemStatus === 'green' ? 'System online' : systemStatus === 'yellow' ? 'System degraded' : 'System offline'"
          style="width:8px; height:8px; border-radius:50%; flex-shrink:0; transition:background 0.4s;"
          :style="{ background: STATUS_COLOR[systemStatus], boxShadow: `0 0 5px ${STATUS_COLOR[systemStatus]}88` }"
        ></span>
        <span v-if="!collapsed" style="font-size:10px; color:var(--sidebar-muted);">Ver 2.10</span>
      </div>
    </div>
  </aside>
</template>
