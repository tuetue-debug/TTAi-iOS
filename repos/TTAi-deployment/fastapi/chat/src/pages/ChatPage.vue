<script setup>
import { ref, watch, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import ChatLayout from '../components/ChatLayout.vue'
import ChatWindow from '../components/ChatWindow.vue'
import { getCurrentUser, logout } from '../lib/auth'
import {
  getConversationDetail,
  getModels,
  getGuestStatus,
} from '../lib/chatApi'

const route = useRoute()
const router = useRouter()

const user = ref(null)
const models = ref([])
const guestRemaining = ref(10)
const convData = ref(null)
const loading = ref(false)
const sidebarRef = ref(null)

const convId = computed(() => {
  const id = route.params.id
  return id === 'new' ? null : id
})

onMounted(async () => {
  // Try to get current user (don't fail if not logged in)
  try { user.value = await getCurrentUser() } catch {}

  // Load models
  try {
    const res = await getModels()
    models.value = res.models || []
  } catch {}

  // Guest status
  if (!user.value) {
    try {
      const gs = await getGuestStatus()
      guestRemaining.value = gs.remaining ?? 10
    } catch {}
  }

  await loadConversation()
})

// Route changes (incl. new-conv redirect during streaming) load silently
// to avoid unmounting ChatWindow and killing the active stream.
watch(() => route.params.id, () => loadConversation(false))

async function loadConversation(showLoading = true) {
  if (!convId.value) {
    convData.value = null
    return
  }
  if (showLoading) loading.value = true
  try {
    convData.value = await getConversationDetail(convId.value)
  } catch {
    convData.value = null
  } finally {
    if (showLoading) loading.value = false
  }
}

async function handleLogout() {
  await logout().catch(() => {})
  user.value = null
  router.push('/login')
}

async function handleConvCreated(newId) {
  // Sidebar reloads conversation list
  sidebarRef.value?.loadConversations()
}

async function handleConvUpdated() {
  sidebarRef.value?.loadConversations()
}
</script>

<template>
  <ChatLayout :user="user" :guest-remaining="guestRemaining" @logout="handleLogout">
    <template #topbar>
      <span class="topbar-title">Chat</span>
    </template>

    <div v-if="loading" style="display: flex; align-items: center; justify-content: center; flex: 1; color: var(--muted);">
      Loading…
    </div>
    <ChatWindow
      v-else
      :conv-id="convId"
      :messages="convData?.messages || []"
      :model="convData?.conversation?.model || (models[0] || 'qwen3:4b')"
      :models="models"
      :user="user"
      :guest-remaining="guestRemaining"
      @conversation-created="handleConvCreated"
      @conv-updated="handleConvUpdated"
    />
  </ChatLayout>
</template>
