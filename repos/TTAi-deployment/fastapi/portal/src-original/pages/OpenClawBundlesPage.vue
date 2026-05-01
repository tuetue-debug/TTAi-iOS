<script setup>
import { onMounted, ref } from 'vue'
import { getOpenClawSetupBundles } from '../lib/openclawSetup'

const loading = ref(true)
const error = ref('')
const bundles = ref([])

onMounted(async () => {
  try {
    const payload = await getOpenClawSetupBundles()
    bundles.value = payload.items || []
  } catch (err) {
    error.value = err?.message || 'Failed to load bundles'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <section class="single-column-grid">
    <article class="panel-card">
      <h3>{{ $t('OpenClawBundlesPage.setupBundles') }}</h3>
      <p>{{ $t('OpenClawBundlesPage.reviewSetupBundlesCreatedFrom') }}</p>
      <p v-if="error" class="form-error">{{ error }}</p>
      <div v-if="loading" class="empty-state">{{ $t('OpenClawBundlesPage.loadingBundles') }}</div>
      <div v-else-if="!bundles.length" class="empty-state">{{ $t('OpenClawBundlesPage.noSetupBundlesCreatedYet') }}</div>
      <div v-else class="key-list">
        <div v-for="bundle in bundles" :key="bundle.id" class="key-item">
          <div>
            <div class="key-name">{{ bundle.name || bundle.id }}</div>
            <div class="key-meta">{{ bundle.preset_name || 'No preset' }} â€¢ {{ bundle.created_at || 'Unknown date' }}</div>
          </div>
        </div>
      </div>
    </article>
  </section>
</template>
