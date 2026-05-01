<script setup>
import { onMounted, ref } from 'vue'
import { getOpenClawStarterPresets } from '../lib/openclawSetup'

const loading = ref(true)
const error = ref('')
const presets = ref([])

onMounted(async () => {
  try {
    const payload = await getOpenClawStarterPresets()
    presets.value = payload.items || []
  } catch (err) {
    error.value = err?.message || 'Failed to load starter presets'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <section class="single-column-grid">
    <article class="panel-card">
      <h3>Starter Presets</h3>
      <p>Preset library for quickly configuring OpenClaw assistant behavior.</p>
      <p v-if="error" class="form-error">{{ error }}</p>
      <div v-if="loading" class="empty-state">Loading presets...</div>
      <div v-else-if="!presets.length" class="empty-state">No starter presets available.</div>
      <div v-else class="endpoint-list">
        <div v-for="preset in presets" :key="preset.id" class="endpoint-item">
          <div class="endpoint-method">PRESET</div>
          <div class="endpoint-path">{{ preset.name }}</div>
          <div class="endpoint-desc">{{ preset.description || 'No description' }}</div>
        </div>
      </div>
    </article>
  </section>
</template>
