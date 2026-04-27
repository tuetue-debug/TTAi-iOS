<script setup>
import { ref, watch, onMounted } from 'vue'

const props = defineProps({
  role: { type: String, required: true },
  content: { type: String, default: '' },
  streaming: { type: Boolean, default: false },
  replyTo: { type: Object, default: null }, // { role, content }
  messageId: { type: String, default: null },
  sources: { type: Array, default: () => [] },
  searchStatus: { type: String, default: '' },
})
const emit = defineEmits(['reply', 'copy-done'])

// ── Markdown / syntax highlight (lazy) ────────────
let markedReady = false
let marked, hljs

async function loadDeps() {
  if (markedReady) return
  const [m, hCore, py, js, ts, bash, json, sql, go, rust, java, cpp, css, xml, yaml] = await Promise.all([
    import('marked'),
    import('highlight.js/lib/core'),
    import('highlight.js/lib/languages/python'),
    import('highlight.js/lib/languages/javascript'),
    import('highlight.js/lib/languages/typescript'),
    import('highlight.js/lib/languages/bash'),
    import('highlight.js/lib/languages/json'),
    import('highlight.js/lib/languages/sql'),
    import('highlight.js/lib/languages/go'),
    import('highlight.js/lib/languages/rust'),
    import('highlight.js/lib/languages/java'),
    import('highlight.js/lib/languages/cpp'),
    import('highlight.js/lib/languages/css'),
    import('highlight.js/lib/languages/xml'),
    import('highlight.js/lib/languages/yaml'),
  ])
  hljs = hCore.default
  const langs = { python: py, javascript: js, typescript: ts, bash, shell: bash, json, sql, go, rust, java, cpp, css, xml, html: xml, yaml }
  for (const [name, mod] of Object.entries(langs)) hljs.registerLanguage(name, mod.default)
  marked = m.marked
  marked.setOptions({
    highlight: (code, lang) => {
      if (lang && hljs.getLanguage(lang)) return hljs.highlight(code, { language: lang }).value
      try { return hljs.highlightAuto(code).value } catch { return code }
    },
    breaks: true,
    gfm: true,
  })
  markedReady = true
}

function escapeHtml(text) {
  return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
}

function renderMarkdown(text) {
  if (!markedReady || !marked) return escapeHtml(text)
  let html = marked.parse(text)
  html = html.replace(
    /<pre><code(?: class="language-(\w+)")?>([\s\S]*?)<\/code><\/pre>/g,
    (_, lang, code) => {
      const langLabel = lang || 'code'
      const rawCode = code.replace(/&lt;/g,'<').replace(/&gt;/g,'>').replace(/&amp;/g,'&').replace(/&#39;/g,"'").replace(/&quot;/g,'"')
      return `<div class="code-block"><div class="code-header"><span>${langLabel}</span><button class="code-copy" data-code="${encodeURIComponent(rawCode)}">Copy</button></div><pre><code class="hljs">${code}</code></pre></div>`
    }
  )
  return html
}

const rendered = ref('')

async function update() {
  await loadDeps()
  rendered.value = props.role === 'assistant' ? renderMarkdown(props.content) : escapeHtml(props.content)
}

watch(() => props.content, update, { immediate: true })
onMounted(() => update())

// ── Code copy (event delegation) ──────────────────
function handleBubbleClick(e) {
  const btn = e.target.closest('.code-copy')
  if (!btn) return
  const code = decodeURIComponent(btn.dataset.code || '')
  navigator.clipboard.writeText(code).then(() => {
    btn.textContent = 'Copied!'
    setTimeout(() => { btn.textContent = 'Copy' }, 2000)
  })
}

// ── Message actions ────────────────────────────────
const copyDone = ref(false)
const showShare = ref(false)
const feedbackDone = ref(null) // 'up' | 'down' | null
const sourcesOpen = ref(false)

function handleCopy() {
  navigator.clipboard.writeText(props.content).then(() => {
    copyDone.value = true
    setTimeout(() => { copyDone.value = false }, 2000)
  })
}

function handleReply() {
  emit('reply', { role: props.role, content: props.content })
}

function handleFeedback(up) {
  if (!props.messageId || feedbackDone.value) return
  feedbackDone.value = up ? 'up' : 'down'
  fetch('/chat-api/feedback', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ message_id: props.messageId, thumbs_up: up }),
  }).catch(() => { feedbackDone.value = null })
}


// ── Share ──────────────────────────────────────────
const CONSOLE_URL = 'https://console.tuetue.vn'

function shareFacebook() {
  const text = props.content.slice(0, 500)
  const url = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(CONSOLE_URL)}&quote=${encodeURIComponent(text)}`
  window.open(url, '_blank', 'width=600,height=500')
  showShare.value = false
}

function shareNative() {
  if (navigator.share) {
    navigator.share({ text: props.content.slice(0, 1000), url: CONSOLE_URL })
    showShare.value = false
  }
}

function copyForTikTok() {
  navigator.clipboard.writeText(props.content.slice(0, 500)).then(() => {
    window.open('https://www.tiktok.com/', '_blank')
    showShare.value = false
  })
}
</script>

<template>
  <div class="message-row" :class="role" @click="handleBubbleClick">

    <div class="msg-label">{{ role === 'user' ? 'You' : 'Trợ lý Tuệ Tuệ' }}</div>

    <!-- Reply quote (if this message is a reply) -->
    <div v-if="replyTo" class="reply-quote" :style="role === 'user' ? 'text-align:right;border-left:none;border-right:3px solid var(--accent);padding:6px 10px' : ''">
      <strong>↩ {{ replyTo.role === 'user' ? 'You' : 'Trợ lý Tuệ Tuệ' }}</strong>
      <span>{{ replyTo.content.slice(0, 120) }}{{ replyTo.content.length > 120 ? '…' : '' }}</span>
    </div>

    <div class="msg-bubble">
      <div v-if="role === 'assistant'" class="msg-content" v-html="rendered" />
      <div v-else class="msg-content" style="white-space: pre-wrap;">{{ content }}</div>
      <div v-if="streaming && role === 'assistant'" class="thinking-wave">
        <span /><span /><span /><span /><span />
      </div>
    </div>

    <!-- Web search status indicator -->
    <div v-if="searchStatus && !content" class="search-status">
      <span class="search-spinner"></span>
      {{ searchStatus }}
    </div>

    <!-- Web search sources card -->
    <div v-if="sources && sources.length" class="sources-card">
      <button class="sources-toggle" @click.stop="sourcesOpen = !sourcesOpen">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
        </svg>
        {{ sources.length }} nguồn tham khảo
        <span class="sources-chevron">{{ sourcesOpen ? '▲' : '▼' }}</span>
      </button>
      <div v-if="sourcesOpen" class="sources-list">
        <a
          v-for="s in sources"
          :key="s.index"
          :href="s.url"
          target="_blank"
          rel="noopener noreferrer"
          class="source-item"
        >
          <span class="source-index">[{{ s.index }}]</span>
          <span class="source-title">{{ s.title }}</span>
        </a>
      </div>
    </div>

    <!-- Hover action bar -->
    <div class="msg-actions" v-if="!streaming">
      <!-- Reply -->
      <button class="msg-action-btn" @click.stop="handleReply" title="Reply">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="9 17 4 12 9 7"/><path d="M20 18v-2a4 4 0 0 0-4-4H4"/>
        </svg>
        Reply
      </button>

      <!-- Copy message -->
      <button class="msg-action-btn" @click.stop="handleCopy" title="Copy text">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
        </svg>
        {{ copyDone ? 'Copied!' : 'Copy' }}
      </button>

      <!-- Share -->
      <button class="msg-action-btn" @click.stop="showShare = true" title="Share">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/>
          <line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/>
        </svg>
        Share
      </button>

      <!-- Feedback (assistant only) -->
      <template v-if="role === 'assistant' && messageId">
        <template v-if="!feedbackDone">
          <button class="msg-action-btn" @click.stop="handleFeedback(true)" title="Câu trả lời tốt">👍</button>
          <button class="msg-action-btn" @click.stop="handleFeedback(false)" title="Câu trả lời chưa tốt">👎</button>
        </template>
        <span v-else class="feedback-done-label">
          {{ feedbackDone === 'up' ? '👍 Cảm ơn!' : '👎 Đã ghi nhận' }}
        </span>
      </template>
    </div>

    <!-- Share popup -->
    <Teleport to="body">
      <div v-if="showShare" class="share-overlay" @click.self="showShare = false">
        <div class="share-popup">
          <div class="share-title">Share this message</div>
          <div class="share-preview">{{ content.slice(0, 160) }}</div>
          <div class="share-grid">

            <!-- Facebook -->
            <button class="share-btn" @click="shareFacebook">
              <div class="share-btn-icon" style="background:#1877f2;">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="white">
                  <path d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z"/>
                </svg>
              </div>
              Share on Facebook
            </button>

            <!-- TikTok (copy + open) -->
            <button class="share-btn" @click="copyForTikTok">
              <div class="share-btn-icon" style="background:#010101;">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="white">
                  <path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-2.88 2.5 2.89 2.89 0 0 1-2.89-2.89 2.89 2.89 0 0 1 2.89-2.89c.28 0 .54.04.79.1V9.01a6.32 6.32 0 0 0-.79-.05 6.34 6.34 0 0 0-6.34 6.34 6.34 6.34 0 0 0 6.34 6.34 6.34 6.34 0 0 0 6.33-6.34V8.69a8.18 8.18 0 0 0 4.78 1.52V6.76a4.85 4.85 0 0 1-1.01-.07z"/>
                </svg>
              </div>
              Copy & open TikTok
            </button>

            <!-- Web Share (mobile) -->
            <button v-if="!!navigator?.share" class="share-btn" @click="shareNative">
              <div class="share-btn-icon" style="background: var(--accent);">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5">
                  <path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8"/><polyline points="16 6 12 2 8 6"/><line x1="12" y1="2" x2="12" y2="15"/>
                </svg>
              </div>
              Share via device
            </button>

          </div>
          <button class="share-close" @click="showShare = false">Cancel</button>
        </div>
      </div>
    </Teleport>

  </div>
</template>
