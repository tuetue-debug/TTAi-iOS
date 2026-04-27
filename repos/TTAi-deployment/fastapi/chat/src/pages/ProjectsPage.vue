<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import ChatLayout from '../components/ChatLayout.vue'
import { getCurrentUser, logout } from '../lib/auth'
import { getProjects, createProject, updateProject, deleteProject } from '../lib/chatApi'

const router = useRouter()
const user = ref(null)
const projects = ref([])
const loading = ref(true)
const error = ref('')
const showNew = ref(false)
const newName = ref('')
const newContext = ref('')
const creating = ref(false)
const editingId = ref(null)
const editName = ref('')
const editContext = ref('')

onMounted(async () => {
  try { user.value = await getCurrentUser() } catch { router.push('/login'); return }
  await reload()
})

async function reload() {
  loading.value = true
  try {
    const res = await getProjects()
    projects.value = res.projects || []
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

async function handleCreate() {
  if (!newName.value.trim()) return
  creating.value = true
  try {
    await createProject(newName.value.trim(), newContext.value.trim())
    newName.value = ''
    newContext.value = ''
    showNew.value = false
    await reload()
  } catch (e) {
    error.value = e.message
  } finally {
    creating.value = false
  }
}

function startEdit(p) {
  editingId.value = p.id
  editName.value = p.name
  editContext.value = p.context || ''
}

async function saveEdit(id) {
  await updateProject(id, { name: editName.value, context: editContext.value })
  editingId.value = null
  await reload()
}

async function handleDelete(id) {
  if (!confirm('Delete this project?')) return
  await deleteProject(id)
  await reload()
}

async function handleLogout() {
  await logout().catch(() => {})
  router.push('/login')
}
</script>

<template>
  <ChatLayout :user="user" @logout="handleLogout">
    <div class="page-shell">
      <div class="page-inner">
        <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:20px;">
          <h1 class="page-title" style="margin:0;">📁 Projects</h1>
          <button class="btn btn-primary" @click="showNew = !showNew">+ New project</button>
        </div>

        <p style="color: var(--muted); font-size: 13px; margin-bottom: 20px;">
          Create project contexts — when you start a chat and select a project,
          TTAi automatically loads its context (tech stack, rules, goals) into the system prompt.
        </p>

        <p v-if="error" style="color: #ef4444; font-size: 13px;">{{ error }}</p>

        <!-- New project form -->
        <div v-if="showNew" class="panel-card" style="margin-bottom: 16px;">
          <div class="form-row">
            <label class="form-label">Project name</label>
            <input class="form-input" v-model="newName" placeholder="e.g. TTAi Platform" />
          </div>
          <div class="form-row">
            <label class="form-label">Context (tech stack, goals, rules…)</label>
            <textarea class="form-textarea" v-model="newContext" placeholder="This project uses Vue 3 + FastAPI. Backend is Python 3.11. Always use TypeScript in frontend code…" rows="4" />
          </div>
          <div style="display: flex; gap: 8px;">
            <button class="btn btn-primary" @click="handleCreate" :disabled="creating">
              {{ creating ? 'Creating…' : 'Create project' }}
            </button>
            <button class="btn" @click="showNew = false">Cancel</button>
          </div>
        </div>

        <div v-if="loading" style="color: var(--muted);">Loading…</div>
        <div v-else-if="!projects.length && !showNew" class="panel-card" style="color: var(--muted); font-size: 13px;">
          No projects yet. Create one to give TTAi persistent project context.
        </div>

        <div v-for="p in projects" :key="p.id" class="proj-item">
          <template v-if="editingId === p.id">
            <div class="form-row">
              <input class="form-input" v-model="editName" />
            </div>
            <div class="form-row">
              <textarea class="form-textarea" v-model="editContext" rows="4" />
            </div>
            <div class="proj-actions">
              <button class="btn btn-primary" @click="saveEdit(p.id)">Save</button>
              <button class="btn" @click="editingId = null">Cancel</button>
            </div>
          </template>
          <template v-else>
            <div class="proj-name">{{ p.name }}</div>
            <div class="proj-context" v-if="p.context">{{ p.context }}</div>
            <div class="proj-actions">
              <button class="btn" @click="startEdit(p)">Edit</button>
              <button class="btn btn-danger" @click="handleDelete(p.id)">Delete</button>
            </div>
          </template>
        </div>
      </div>
    </div>
  </ChatLayout>
</template>
