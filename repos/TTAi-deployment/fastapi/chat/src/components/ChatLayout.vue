<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useTheme } from '../composables/useTheme'
import ChatSidebar from './ChatSidebar.vue'

const props = defineProps({
  user: { type: Object, default: null },
  guestRemaining: { type: Number, default: 10 },
})
const emit = defineEmits(['logout'])

const router = useRouter()
const route = useRoute()
const { theme, toggleTheme } = useTheme()

const sidebarCollapsed = ref(window.innerWidth < 900)
const mobileSidebarOpen = ref(false)
const isMobile = ref(window.innerWidth < 641)

onMounted(() => {
  window.addEventListener('resize', () => {
    isMobile.value = window.innerWidth < 641
    if (window.innerWidth >= 641) mobileSidebarOpen.value = false
  })
})

function toggleSidebar() {
  if (isMobile.value) {
    mobileSidebarOpen.value = !mobileSidebarOpen.value
  } else {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }
}
</script>

<template>
  <div class="chat-shell">
    <!-- Mobile overlay -->
    <div
      v-if="isMobile && mobileSidebarOpen"
      class="sidebar-overlay"
      @click="mobileSidebarOpen = false"
    />

    <!-- Sidebar -->
    <ChatSidebar
      :class="[
        'sidebar',
        sidebarCollapsed && !isMobile ? 'collapsed' : '',
        isMobile && mobileSidebarOpen ? 'open' : '',
      ]"
      :collapsed="sidebarCollapsed && !isMobile"
      :user="user"
      :current-conv-id="route.params.id"
      @new-chat="router.push('/c/new')"
      @logout="emit('logout')"
    />

    <!-- Main -->
    <div class="chat-main">
      <!-- Top bar -->
      <div class="chat-topbar">
        <button class="icon-btn" @click="toggleSidebar" title="Toggle sidebar" style="flex-shrink:0;">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/>
          </svg>
        </button>
        <slot name="topbar" />
        <div class="topbar-spacer" />
        <div class="topbar-actions">
          <button class="icon-btn" @click="toggleTheme" :title="theme === 'dark' ? 'Light mode' : 'Dark mode'">
            <span v-if="theme === 'dark'">☀️</span>
            <span v-else>🌙</span>
          </button>
          <a
            href="https://console.tuetue.vn"
            target="_blank"
            class="icon-btn"
            title="Go to Console"
            style="font-size: 12px; font-weight: 600; text-decoration: none;"
          >Console ↗</a>
        </div>
      </div>

      <!-- Content -->
      <slot />

    </div>
  </div>
</template>
