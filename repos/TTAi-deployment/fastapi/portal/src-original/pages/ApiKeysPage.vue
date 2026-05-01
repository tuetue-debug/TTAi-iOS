<script setup>
import { reactive, ref } from 'vue'
import CopyButton from '../components/CopyButton.vue'
import { createPortalApiKey, getPortalOverview, revokePortalApiKey } from '../lib/portalData'

const props = defineProps({
  overview: { type: Object, required: true },
})

const creatingKey = ref(false)
const error = ref('')
const newKey = ref(null)
const apiKeyForm = reactive({
  name: 'Default key',
  scopes: 'chat:generate,usage:read',
})

async function handleCreateKey() {
  error.value = ''
  creatingKey.value = true
  newKey.value = null
  try {
    const payload = await createPortalApiKey({
      name: apiKeyForm.name,
      scopes: apiKeyForm.scopes.split(',').map((item) => item.trim()).filter(Boolean),
    })
    newKey.value = payload.item
    const refreshed = await getPortalOverview()
    Object.assign(props.overview, refreshed)
  } catch (err) {
    error.value = err?.message || 'API key creation failed'
  } finally {
    creatingKey.value = false
  }
}

async function handleRevokeKey(keyId) {
  error.value = ''
  try {
    await revokePortalApiKey(keyId)
    const refreshed = await getPortalOverview()
    Object.assign(props.overview, refreshed)
  } catch (err) {
    error.value = err?.message || 'API key revoke failed'
  }
}
</script>

<template>
  <section class="single-column-grid">
    <article class="panel-card">
      <h3>{{ $t('ApiKeysPage.createApiKey') }}</h3>
      <p>{{ $t('ApiKeysPage.generateRealKeyFromThe') }}</p>
      <form class="auth-form" @submit.prevent="handleCreateKey">
        <label>
          <span>{{ $t('ApiKeysPage.keyName') }}</span>
          <input v-model="apiKeyForm.name" type="text" :placeholder="$t('ApiKeysPage.productionKey')" />
        </label>
        <label>
          <span>{{ $t('ApiKeysPage.scopesCommaSeparated') }}</span>
          <input v-model="apiKeyForm.scopes" type="text" :placeholder="$t('ApiKeysPage.chatgenerateusageread')" />
        </label>
        <button class="primary-btn full" :disabled="creatingKey">
          {{ creatingKey ? 'Creating keyâ€¦' : 'Create API key' }}
        </button>
        <p v-if="error" class="form-error">{{ error }}</p>
      </form>

      <div v-if="newKey" class="key-reveal">
        <div class="inline-row between">
          <div class="preview-label">{{ $t('ApiKeysPage.newKeyShownOnce') }}</div>
          <CopyButton :text="newKey.key" label="Copy key" />
        </div>
        <code>{{ newKey.key }}</code>
      </div>
    </article>

    <article class="panel-card">
      <h3>{{ $t('ApiKeysPage.yourApiKeys') }}</h3>
      <p>{{ $t('ApiKeysPage.liveDataFromTheAccount') }}</p>
      <div v-if="!(overview?.api_keys?.items || []).length" class="empty-state">{{ $t('ApiKeysPage.noApiKeysYet') }}</div>
      <div v-else class="key-list">
        <div v-for="item in overview.api_keys.items" :key="item.id" class="key-item">
          <div>
            <div class="key-name">{{ item.name }}</div>
            <div class="key-meta">{{ item.key_prefix }} â€¢ {{ item.scopes.join(', ') || 'no scopes' }}</div>
          </div>
          <button class="ghost-btn" @click="handleRevokeKey(item.id)">{{ $t('ApiKeysPage.revoke') }}</button>
        </div>
      </div>
    </article>
  </section>
</template>
