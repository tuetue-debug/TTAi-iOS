<script setup>
import { computed, onMounted, ref } from 'vue'
import CopyButton from '../components/CopyButton.vue'
import { getPortalDocs } from '../lib/portalDocs'

const loading = ref(true)
const error = ref('')
const docs = ref(null)
const activeTab = ref('overview')

const tabs = [
  { key: 'overview', label: 'Overview' },
  { key: 'reference', label: 'Reference' },
]

onMounted(async () => {
  try {
    docs.value = await getPortalDocs()
  } catch (err) {
    error.value = err?.message || 'Failed to load docs'
  } finally {
    loading.value = false
  }
})

function selectTab(tabKey) {
  activeTab.value = tabKey
}

const docsTheme = computed(() => document.documentElement.classList.contains('theme-dark') ? 'dark' : 'light')
const referenceUrl = computed(() => `/docs?embed=1&theme=${docsTheme.value}&v=20260424d`)
</script>

<template>
  <section class="single-column-grid">
    <article class="panel-card integrations-shell docs-shell-page">
      <div class="integrations-header">
        <div>
          <div class="eyebrow">{{ $t('DocsPage.docs') }}</div>
          <h3>{{ $t('DocsPage.ttaiDeveloperDocumentation') }}</h3>
          <p class="integrations-subtitle">
            Quickstart guidance and interactive reference in one console workspace.
          </p>
        </div>
      </div>

      <div class="integrations-tabs" role="tablist" aria-label="Docs sections">
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

      <p v-if="error" class="form-error">{{ error }}</p>
      <div v-if="loading" class="empty-state">Loading documentation…</div>

      <template v-else>
        <template v-if="activeTab === 'overview'">
          <div class="integrations-resource-grid docs-overview-grid">
            <article class="panel-subtle">
              <div class="preview-label">{{ $t('DocsPage.workspaceResources') }}</div>
              <div class="resource-list">
                <div class="resource-item">
                  <div>
                    <strong>{{ $t('DocsPage.console') }}</strong>
                    <div class="resource-value">https://console.tuetue.vn</div>
                  </div>
                  <a class="ghost-btn link-btn" href="https://console.tuetue.vn" target="_blank" rel="noreferrer">{{ $t('OpenClawSetupPage.open_1') }}</a>
                </div>
                <div class="resource-item">
                  <div>
                    <strong>{{ $t('OpenClawSetupPage.apiBaseUrl') }}</strong>
                    <div class="resource-value">{{ docs?.base_url || 'https://api.tuetue.vn' }}</div>
                  </div>
                  <CopyButton :text="docs?.base_url || 'https://api.tuetue.vn'" label="Copy" />
                </div>
                <div class="resource-item">
                  <div>
                    <strong>{{ $t('DocsPage.openapiSchema') }}</strong>
                    <div class="resource-value">https://console.tuetue.vn/openapi.json</div>
                  </div>
                  <div class="inline-row">
                    <CopyButton text="https://console.tuetue.vn/openapi.json" label="Copy" />
                    <a class="ghost-btn link-btn" href="https://console.tuetue.vn/openapi.json" target="_blank" rel="noreferrer">{{ $t('OpenClawSetupPage.open_1') }}</a>
                  </div>
                </div>
                <div class="resource-item">
                  <div>
                    <strong>{{ $t('DocsPage.authentication') }}</strong>
                    <div class="resource-value">Authorization: Bearer YOUR_API_KEY</div>
                  </div>
                  <CopyButton text="Authorization: Bearer YOUR_API_KEY" label="Copy" />
                </div>
              </div>
            </article>

            <article class="panel-subtle">
              <div class="preview-label">{{ $t('OverviewPage.quickStart') }}</div>
              <div class="endpoint-list compact-list">
                <div class="endpoint-item">
                  <div class="endpoint-method">1</div>
                  <div class="endpoint-path">{{ $t('DocsPage.createAnApiKey') }}</div>
                  <div class="endpoint-desc">{{ $t('DocsPage.useTheApiKeysSection') }}</div>
                </div>
                <div class="endpoint-item">
                  <div class="endpoint-method">2</div>
                  <div class="endpoint-path">{{ $t('DocsPage.useTheRuntimeBaseUrl') }}</div>
                  <div class="endpoint-desc">{{ $t('DocsPage.sendRequestsTo') }} <code>https://api.tuetue.vn</code>.</div>
                </div>
                <div class="endpoint-item">
                  <div class="endpoint-method">3</div>
                  <div class="endpoint-path">{{ $t('DocsPage.testInReference') }}</div>
                  <div class="endpoint-desc">{{ $t('DocsPage.switchToTheReferenceTab') }}</div>
                </div>
              </div>
            </article>
          </div>

          <div class="docs-code-grid">
            <div class="code-block">
              <div class="code-label-row">
                <div class="code-label">curl</div>
                <CopyButton :text="docs?.quickstart?.curl || ''" label="Copy" />
              </div>
              <pre><code>{{ docs?.quickstart?.curl }}</code></pre>
            </div>
            <div class="code-block">
              <div class="code-label-row">
                <div class="code-label">{{ $t('DocsPage.javascript') }}</div>
                <CopyButton :text="docs?.quickstart?.javascript || ''" label="Copy" />
              </div>
              <pre><code>{{ docs?.quickstart?.javascript }}</code></pre>
            </div>
            <div class="code-block">
              <div class="code-label-row">
                <div class="code-label">{{ $t('DocsPage.python') }}</div>
                <CopyButton :text="docs?.quickstart?.python || ''" label="Copy" />
              </div>
              <pre><code>{{ docs?.quickstart?.python }}</code></pre>
            </div>
          </div>

          <div class="integrations-panel-head" style="margin-top: 12px;">
            <div>
              <h4>{{ $t('DocsPage.keyEndpoints') }}</h4>
              <p>{{ $t('DocsPage.mostusedPathsForPortalAnd') }}</p>
            </div>
          </div>
          <div class="endpoint-list integrations-list">
            <div v-for="ep in docs?.endpoints" :key="ep.name" class="endpoint-item">
              <div class="endpoint-method">{{ ep.method }}</div>
              <div class="endpoint-path">{{ ep.path }}</div>
              <div class="endpoint-desc">{{ ep.description }}</div>
            </div>
          </div>
        </template>

        <template v-else-if="activeTab === 'reference'">
          <div class="docs-embedded-reference docs-embedded-reference-flat">
            <div class="docs-embed-shell docs-embed-shell-flat">
              <iframe
                :key="referenceUrl"
                class="docs-embed-frame docs-embed-frame-flat"
                :src="referenceUrl"
                title="TTAi developer docs"
                loading="lazy"
                referrerpolicy="no-referrer"
              ></iframe>
            </div>
          </div>
        </template>
      </template>
    </article>
  </section>
</template>
