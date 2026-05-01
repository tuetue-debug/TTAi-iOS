<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import CopyButton from '../components/CopyButton.vue'
import {
  createOpenClawSetupBundle,
  deleteOpenClawSetupBundle,
  getOpenClawSetupBundles,
  getOpenClawStarterPresets,
  previewOpenClawSetup,
} from '../lib/openclawSetup'

const loading = ref(true)
const creating = ref(false)
const deletingBundleId = ref('')
const previewLoading = ref(false)
const error = ref('')
const success = ref('')
const presets = ref([])
const bundles = ref([])
const preview = ref(null)
const created = ref(null)
const activeTab = ref('setup')

const tabs = [
  { key: 'setup', label: 'Setup' },
  { key: 'bundles', label: 'Bundles' },
  { key: 'presets', label: 'Presets' },
  { key: 'targets', label: 'Targets' },
]

const form = reactive({
  bundle_name: 'Default integration setup',
  preset_id: '',
  assistant_name: 'Tuá»‡ Tuá»‡',
  user_name: 'Tuá»‡ VÄƒn',
  project_name: 'TTAi Workspace',
})

const selectedPreset = computed(() => presets.value.find((p) => p.id === form.preset_id) || null)
const openApiUrl = 'https://console.tuetue.vn/openapi.json'
const docsUrl = 'https://console.tuetue.vn/docs'
const baseApiUrl = 'https://api.tuetue.vn'

let previewTimer = null

async function loadAll() {
  loading.value = true
  error.value = ''
  try {
    const [presetPayload, bundlePayload] = await Promise.all([
      getOpenClawStarterPresets(),
      getOpenClawSetupBundles(),
    ])
    presets.value = presetPayload.items || []
    bundles.value = bundlePayload.items || []
    if (presets.value.length && !form.preset_id) {
      form.preset_id = presets.value[0].id
    }
    await refreshPreview()
  } catch (err) {
    error.value = err?.message || 'Failed to load integrations data'
  } finally {
    loading.value = false
  }
}

onMounted(loadAll)

watch(
  () => [form.bundle_name, form.preset_id, form.assistant_name, form.user_name, form.project_name],
  () => {
    if (loading.value) return
    clearTimeout(previewTimer)
    previewTimer = setTimeout(() => {
      refreshPreview()
    }, 250)
  }
)

function selectTab(tabKey) {
  activeTab.value = tabKey
  error.value = ''
  success.value = ''
}

async function refreshPreview() {
  previewLoading.value = true
  try {
    const payload = await previewOpenClawSetup({ ...form })
    preview.value = payload.preview || null
  } catch (err) {
    error.value = err?.message || 'Preview failed'
  } finally {
    previewLoading.value = false
  }
}

async function handleCreate() {
  error.value = ''
  success.value = ''
  creating.value = true
  try {
    const payload = await createOpenClawSetupBundle({ ...form })
    created.value = payload.item || null
    success.value = 'Bundle created successfully.'
    await loadAll()
    activeTab.value = 'bundles'
  } catch (err) {
    error.value = err?.message || 'Bundle creation failed'
  } finally {
    creating.value = false
  }
}

async function handleDelete(bundleId) {
  const confirmed = window.confirm('Delete this bundle?')
  if (!confirmed) return

  error.value = ''
  success.value = ''
  deletingBundleId.value = bundleId
  try {
    await deleteOpenClawSetupBundle(bundleId)
    bundles.value = bundles.value.filter((bundle) => bundle.id !== bundleId)
    success.value = 'Bundle deleted successfully.'
  } catch (err) {
    error.value = err?.message || 'Bundle deletion failed'
  } finally {
    deletingBundleId.value = ''
  }
}
</script>

<template>
  <section class="single-column-grid">
    <article class="panel-card integrations-shell">
      <div class="integrations-header">
        <div>
          <div class="eyebrow">{{ $t('OpenClawSetupPage.integrations') }}</div>
          <h3>{{ $t('OpenClawSetupPage.manageSetupFlowsPresetsAnd') }}</h3>
          <p class="integrations-subtitle">
            Build reusable configurations for OpenClaw and future app, plugin, or chat targets from one shared workspace.
          </p>
        </div>
      </div>

      <div class="integrations-tabs" role="tablist" :aria-label="$t('OpenClawSetupPage.integrationsSections')">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          class="tab-chip"
          :class="{ active: activeTab === tab.key }"
          @click="selectTab(tab.key)"
        >
          {{ tab.label }}
        </button>
      </div>

      <div v-if="activeTab === 'setup'" class="integrations-subactions">
        <button class="primary-action-btn" type="button" @click="handleCreate" :disabled="creating">
          {{ creating ? 'Creating...' : 'Create bundle' }}
        </button>
      </div>

      <p v-if="error" class="form-error">{{ error }}</p>
      <p v-if="success" class="form-success">{{ success }}</p>
      <div v-if="loading" class="empty-state">{{ $t('OpenClawSetupPage.loadingIntegrations') }}</div>

      <template v-else>
        <template v-if="activeTab === 'setup'">
          <div class="integrations-panel-head">
            <div>
              <h4>{{ $t('OpenClawSetupPage.setup') }}</h4>
              <p>{{ $t('OpenClawSetupPage.createConfigurationBundleUsingPreset') }}</p>
            </div>
          </div>

          <div class="integrations-grid single-stack">
            <form class="auth-form panel-subtle integrations-form-grid" @submit.prevent="handleCreate">
              <label>
                <span>{{ $t('OpenClawSetupPage.name') }}</span>
                <input v-model="form.bundle_name" type="text" :placeholder="$t('OpenClawSetupPage.defaultIntegrationSetup')" />
              </label>
              <label>
                <span>{{ $t('OpenClawSetupPage.preset') }}</span>
                <select v-model="form.preset_id">
                  <option value="" disabled>{{ $t('OpenClawSetupPage.selectPreset') }}</option>
                  <option v-for="preset in presets" :key="preset.id" :value="preset.id">
                    {{ preset.name }}
                  </option>
                </select>
              </label>
              <label>
                <span>{{ $t('OpenClawSetupPage.assistant') }}</span>
                <input v-model="form.assistant_name" type="text" placeholder="Tuá»‡ Tuá»‡" />
              </label>
              <label>
                <span>{{ $t('OpenClawSetupPage.user') }}</span>
                <input v-model="form.user_name" type="text" placeholder="Tuá»‡ VÄƒn" />
              </label>
              <label>
                <span>{{ $t('OpenClawSetupPage.project') }}</span>
                <input v-model="form.project_name" type="text" :placeholder="$t('OpenClawSetupPage.ttaiWorkspace')" />
              </label>
            </form>

            <div class="panel-subtle">
              <h4>{{ $t('OpenClawSetupPage.details') }}</h4>
              <div v-if="selectedPreset" class="detail-list compact">
                <div class="detail-item compact">
                  <span>{{ $t('OpenClawSetupPage.preset') }}</span>
                  <strong>{{ selectedPreset.name }}</strong>
                </div>
                <div class="detail-item compact">
                  <span>{{ $t('OpenClawSetupPage.description') }}</span>
                  <strong>{{ selectedPreset.description || 'No description' }}</strong>
                </div>
              </div>
              <div v-else class="empty-state compact">{{ $t('OpenClawSetupPage.selectPresetToViewDetails') }}</div>
            </div>

            <div class="panel-subtle">
              <div class="integrations-panel-head compact-head">
                <div>
                  <h4>{{ $t('OpenClawSetupPage.preview') }}</h4>
                  <p>{{ $t('OpenClawSetupPage.generatedAutomaticallyFromTheCurrent') }}</p>
                </div>
                <div v-if="previewLoading" class="panel-meta-note">{{ $t('OpenClawSetupPage.updating') }}</div>
              </div>
              <div v-if="preview" class="preview-block">
                <pre><code>{{ JSON.stringify(preview, null, 2) }}</code></pre>
              </div>
              <div v-else class="empty-state compact">{{ $t('OpenClawSetupPage.previewIsNotAvailableYet') }}</div>
            </div>
          </div>

          <article v-if="created" class="panel-subtle" style="margin-top: 20px;">
            <div class="preview-label">{{ $t('OpenClawSetupPage.createdBundle') }}</div>
            <pre><code>{{ JSON.stringify(created, null, 2) }}</code></pre>
          </article>
        </template>

        <template v-else-if="activeTab === 'bundles'">
          <div class="integrations-panel-head">
            <div>
              <h4>{{ $t('OpenClawSetupPage.bundles') }}</h4>
              <p>{{ $t('OpenClawSetupPage.reviewConfigurationsCreatedFromThis') }}</p>
            </div>
          </div>

          <div class="integrations-panel-toolbar">
            <div></div>
            <button class="ghost-btn panel-cta-btn" type="button" @click="selectTab('setup')">{{ $t('OpenClawSetupPage.createBundle') }}</button>
          </div>

          <div v-if="!bundles.length" class="empty-state">
            <div>{{ $t('OpenClawSetupPage.noBundlesYet') }}</div>
            <button class="ghost-btn panel-cta-btn" type="button" @click="selectTab('setup')">{{ $t('OpenClawSetupPage.goToSetup') }}</button>
          </div>
          <div v-else class="key-list integrations-list">
            <div v-for="bundle in bundles" :key="bundle.id" class="key-item bundle-item">
              <div>
                <div class="key-name">{{ bundle.name || bundle.id }}</div>
                <div class="key-meta">{{ bundle.preset_name || 'No preset' }} â€¢ {{ bundle.created_at || 'Unknown date' }}</div>
              </div>
              <div class="bundle-item-actions">
                <div class="list-status">{{ bundle.status || 'created' }}</div>
                <button
                  class="ghost-btn delete-btn"
                  type="button"
                  @click="handleDelete(bundle.id)"
                  :disabled="deletingBundleId === bundle.id"
                >
                  {{ deletingBundleId === bundle.id ? 'Deleting...' : 'Delete' }}
                </button>
              </div>
            </div>
          </div>
        </template>

        <template v-else-if="activeTab === 'presets'">
          <div class="integrations-panel-head">
            <div>
              <h4>{{ $t('OpenClawSetupPage.presets') }}</h4>
              <p>{{ $t('OpenClawSetupPage.reusableStartingPointsForSetup') }}</p>
            </div>
          </div>

          <div v-if="!presets.length" class="empty-state">{{ $t('OpenClawSetupPage.noPresetsAvailable') }}</div>
          <div v-else class="endpoint-list integrations-list">
            <div v-for="preset in presets" :key="preset.id" class="endpoint-item">
              <div class="endpoint-method">{{ $t('OpenClawSetupPage.preset') }}</div>
              <div class="endpoint-path">{{ preset.name }}</div>
              <div class="endpoint-desc">{{ preset.description || 'No description' }}</div>
            </div>
          </div>
        </template>

        <template v-else-if="activeTab === 'targets'">
          <div class="integrations-panel-head">
            <div>
              <h4>{{ $t('OpenClawSetupPage.targets') }}</h4>
              <p>{{ $t('OpenClawSetupPage.futureExecutionDestinationsForThis') }}</p>
            </div>
          </div>

          <div class="endpoint-list integrations-list">
            <div class="endpoint-item">
              <div class="endpoint-method">{{ $t('OpenClawSetupPage.target') }}</div>
              <div class="endpoint-path">{{ $t('OpenClawSetupPage.openclaw') }}</div>
              <div class="endpoint-desc">{{ $t('OpenClawSetupPage.importSetupBundlesIntoAn') }}</div>
            </div>
            <div class="endpoint-item">
              <div class="endpoint-method">{{ $t('OpenClawSetupPage.target') }}</div>
              <div class="endpoint-path">{{ $t('OpenClawSetupPage.chatPluginWidget') }}</div>
              <div class="endpoint-desc">{{ $t('OpenClawSetupPage.prepareConnectionFlowsForChat') }}</div>
            </div>
            <div class="endpoint-item">
              <div class="endpoint-method">{{ $t('OpenClawSetupPage.target') }}</div>
              <div class="endpoint-path">{{ $t('OpenClawSetupPage.appSdk') }}</div>
              <div class="endpoint-desc">{{ $t('OpenClawSetupPage.prepareIntegrationPayloadsForApps') }}</div>
            </div>
          </div>
        </template>
      </template>

      <div class="integrations-footer-tools">
        <article class="panel-subtle integrations-utility-card">
          <div class="preview-label">{{ $t('OpenClawSetupPage.resources') }}</div>
          <div class="resource-list compact-resource-list">
            <div class="resource-item">
              <div>
                <strong>{{ $t('OpenClawSetupPage.apiBaseUrl') }}</strong>
                <div class="resource-value">{{ baseApiUrl }}</div>
              </div>
              <CopyButton :text="baseApiUrl" label="Copy" />
            </div>
            <div class="resource-item">
              <div>
                <strong>{{ $t('OpenClawSetupPage.openapiSpec') }}</strong>
                <div class="resource-value">{{ openApiUrl }}</div>
              </div>
              <div class="inline-row">
                <CopyButton :text="openApiUrl" label="Copy" />
                <a class="ghost-btn link-btn" :href="openApiUrl" target="_blank" rel="noreferrer">{{ $t('OpenClawSetupPage.open') }}</a>
              </div>
            </div>
            <div class="resource-item">
              <div>
                <strong>{{ $t('OpenClawSetupPage.docs') }}</strong>
                <div class="resource-value">{{ docsUrl }}</div>
              </div>
              <div class="inline-row">
                <CopyButton :text="docsUrl" label="Copy" />
                <a class="ghost-btn link-btn" :href="docsUrl" target="_blank" rel="noreferrer">{{ $t('OpenClawSetupPage.open') }}</a>
              </div>
            </div>
          </div>
        </article>
      </div>
    </article>
  </section>
</template>
