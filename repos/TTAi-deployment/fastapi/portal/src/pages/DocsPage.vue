<script setup>
import { onMounted, ref } from 'vue'
import CopyButton from '../components/CopyButton.vue'
import { getPortalDocs } from '../lib/portalDocs'

const loading = ref(true)
const error = ref('')
const docs = ref(null)

onMounted(async () => {
  try {
    docs.value = await getPortalDocs()
  } catch (err) {
    error.value = err?.message || 'Failed to load docs'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <section class="single-column-grid">
    <article class="panel-card">
      <h3>API Reference</h3>
      <p>Live endpoints for TTAi API. Use your API key to authenticate.</p>
      <p v-if="error" class="form-error">{{ error }}</p>
      <div v-if="loading" class="empty-state">Loading API reference…</div>
      <div v-else>
        <div class="detail-item">
          <span>Console</span>
          <strong>https://console.tuetue.vn</strong>
        </div>
        <div class="detail-item">
          <span>Base URL</span>
          <strong>{{ docs?.base_url || 'https://api.tuetue.vn' }}</strong>
        </div>
        <div class="detail-item">
          <span>Authentication</span>
          <strong>Authorization: Bearer YOUR_API_KEY</strong>
        </div>

        <h4 style="margin-top: 28px; margin-bottom: 12px;">Thông tin kết nối cho khách hàng</h4>
        <div class="endpoint-list" style="margin-bottom: 28px;">
          <div class="endpoint-item">
            <div class="endpoint-method">CONSOLE</div>
            <div class="endpoint-path">https://console.tuetue.vn</div>
            <div class="endpoint-desc">Đăng ký, đăng nhập, tạo API key, xem usage, billing, limits, và đọc docs.</div>
          </div>
          <div class="endpoint-item">
            <div class="endpoint-method">API</div>
            <div class="endpoint-path">https://api.tuetue.vn</div>
            <div class="endpoint-desc">Base URL dành cho ứng dụng, SDK, backend service, và tích hợp production.</div>
          </div>
          <div class="endpoint-item">
            <div class="endpoint-method">AUTH</div>
            <div class="endpoint-path">Authorization: Bearer YOUR_API_KEY</div>
            <div class="endpoint-desc">Gửi API key qua header Bearer token cho mọi request cần xác thực.</div>
          </div>
          <div class="endpoint-item">
            <div class="endpoint-method">CHAT</div>
            <div class="endpoint-path">POST /chat</div>
            <div class="endpoint-desc">Endpoint khởi đầu để gửi message vào TTAi API.</div>
          </div>
        </div>

        <h4 style="margin-top: 28px; margin-bottom: 12px;">Quick start</h4>
        <div class="code-block">
          <div class="code-label-row">
            <div class="code-label">curl</div>
            <CopyButton :text="docs?.quickstart?.curl || ''" label="Copy" />
          </div>
          <pre><code>{{ docs?.quickstart?.curl }}</code></pre>
        </div>
        <div class="code-block">
          <div class="code-label-row">
            <div class="code-label">JavaScript</div>
            <CopyButton :text="docs?.quickstart?.javascript || ''" label="Copy" />
          </div>
          <pre><code>{{ docs?.quickstart?.javascript }}</code></pre>
        </div>
        <div class="code-block">
          <div class="code-label-row">
            <div class="code-label">Python</div>
            <CopyButton :text="docs?.quickstart?.python || ''" label="Copy" />
          </div>
          <pre><code>{{ docs?.quickstart?.python }}</code></pre>
        </div>

        <h4 style="margin-top: 28px; margin-bottom: 12px;">Endpoints</h4>
        <div class="endpoint-list">
          <div v-for="ep in docs?.endpoints" :key="ep.name" class="endpoint-item">
            <div class="endpoint-method">{{ ep.method }}</div>
            <div class="endpoint-path">{{ ep.path }}</div>
            <div class="endpoint-desc">{{ ep.description }}</div>
          </div>
        </div>
      </div>
    </article>
  </section>
</template>
