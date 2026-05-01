<script setup>
import { ref, computed, nextTick } from 'vue'
import { RouterLink } from 'vue-router'

const MAX_DEMO = 5

function getGuestId() {
  let id = localStorage.getItem('ttai_guest_id')
  if (!id) { id = crypto.randomUUID(); localStorage.setItem('ttai_guest_id', id) }
  return id
}

const messages      = ref([])
const input         = ref('')
const streaming     = ref(false)
const streamingText = ref('')
const convId        = ref(null)
const error         = ref('')
const inputEl       = ref(null)
const messagesEl    = ref(null)
const isActive      = ref(false)
const demoCount     = ref(0)

const atLimit    = computed(() => demoCount.value >= MAX_DEMO)
const remaining  = computed(() => MAX_DEMO - demoCount.value)

const SUGGESTIONS = [
  '✍️ Write a Python snippet using Tue Tue API',
  '🔍 What can Tue Tue AI do for my business?',
  '⚡ How fast is the Tue Tue model?',
  '🔑 How do I get an API key?',
]

async function ensureConv() {
  if (convId.value) return
  const res = await fetch('/chat-api/conversations', {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', 'X-Guest-Session': getGuestId() },
    body: JSON.stringify({ model: 'tuetue4:e4b-v3' }),
  })
  if (!res.ok) throw new Error('Could not start session')
  convId.value = (await res.json()).id
}

async function submit(text) {
  const content = (typeof text === 'string' ? text : input.value).trim()
  if (!content || streaming.value || atLimit.value) return

  isActive.value = true
  error.value    = ''
  input.value    = ''
  if (inputEl.value) { inputEl.value.style.height = '44px' }

  messages.value.push({ role: 'user', content })
  demoCount.value++
  scrollToBottom()

  streaming.value = true
  streamingText.value = ''

  try {
    await ensureConv()

    const res = await fetch(`/chat-api/conversations/${convId.value}/messages`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json', 'X-Guest-Session': getGuestId() },
      body: JSON.stringify({ content, model: 'tuetue4:e4b-v3' }),
    })
    if (!res.ok) {
      const e = await res.json().catch(() => ({ detail: res.statusText }))
      throw new Error(e.detail || `Error ${res.status}`)
    }

    const reader  = res.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop()
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const d = JSON.parse(line.slice(6))
            if (d.content) { streamingText.value += d.content; scrollToBottom() }
          } catch {}
        }
      }
    }
    messages.value.push({ role: 'assistant', content: streamingText.value })
    streamingText.value = ''
  } catch (err) {
    error.value = err.message || 'Something went wrong. Please try again.'
    messages.value.pop()
    demoCount.value--
  } finally {
    streaming.value = false
    scrollToBottom()
    nextTick(() => inputEl.value?.focus())
  }
}

function scrollToBottom() {
  nextTick(() => { if (messagesEl.value) messagesEl.value.scrollTop = messagesEl.value.scrollHeight })
}

function autoResize() {
  if (!inputEl.value || !isActive.value) return
  inputEl.value.style.height = 'auto'
  inputEl.value.style.height = Math.min(inputEl.value.scrollHeight, 180) + 'px'
}

function handleKey(e) {
  if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) { e.preventDefault(); submit() }
}
</script>

<template>
  <div class="lc">
    <!-- ── Status indicator ── -->
    <div class="lc-status-bar">
      <span class="lc-status-dot"/>
      <span class="lc-status-text">{{ $t('LandingChat.online') }}</span>
    </div>

    <!-- ── Messages ── -->
    <div class="lc-messages" ref="messagesEl">
      <div v-if="!isActive" class="lc-intro">
        <h3 class="lc-intro-title">{{ $t('LandingChat.heroTitle') || 'How can Tue Tue AI help you today?' }}</h3>
        <p class="lc-intro-sub">{{ $t('LandingChat.heroSubtitle') || 'Ask anything — code, analysis, writing, math, and more.' }}</p>
      </div>

      <template v-if="isActive">
        <div v-for="(msg, i) in messages" :key="i" :class="['lc-msg', msg.role === 'user' ? 'lc-user' : 'lc-ai']">
          <div class="lc-bubble">{{ msg.content }}</div>
        </div>
        <div v-if="streaming && streamingText" class="lc-msg lc-ai">
          <div class="lc-bubble lc-streaming">{{ streamingText }}</div>
        </div>
        <div v-if="streaming && !streamingText" class="lc-msg lc-ai">
          <div class="lc-bubble lc-typing"><span/><span/><span/></div>
        </div>
      </template>
    </div>

    <!-- ── Sign-in nudge (at limit) ── -->
    <div v-if="atLimit" class="lc-limit">
      <div class="lc-limit-icon">🔒</div>
      <p>Bạn đã dùng hết <strong>{{ MAX_DEMO }} lượt</strong> thử miễn phí.<br>Đăng nhập để tiếp tục không giới hạn.</p>
      <div class="lc-limit-btns">
        <RouterLink class="primary-btn link-btn" to="/signup">Tạo tài khoản miễn phí</RouterLink>
        <RouterLink class="ghost-btn link-btn" to="/login">Đăng nhập</RouterLink>
      </div>
    </div>

    <!-- ── Input area ── -->
    <div :class="['lc-input-area', isActive ? 'lc-input-active' : 'lc-input-idle']">
      <p v-if="error" class="lc-error">{{ error }}</p>

      <div v-if="!isActive" class="lc-suggestions">
        <button v-for="s in SUGGESTIONS" :key="s" class="lc-chip" @click="submit(s)">{{ s }}</button>
      </div>

      <div class="lc-row">
        <textarea
          ref="inputEl"
          v-model="input"
          :class="['lc-textarea', isActive ? 'lc-ta-active' : 'lc-ta-idle']"
          :placeholder="isActive ? ($t('LandingChat.askFollowUp') || 'Ask a follow-up...') : ($t('LandingChat.askAnything') || 'Ask Tue Tue anything...')"
          :disabled="streaming || atLimit"
          @keydown="handleKey"
          @input="autoResize"
        />
        <button class="lc-send" :disabled="!input.trim() || streaming" @click="submit()">
          <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2.2">
            <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z"/>
          </svg>
        </button>
      </div>

    </div>
  </div>
</template>

<style scoped>
.lc {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  position: relative;
}

/* Status indicator */
.lc-status-bar {
  position: absolute;
  top: 14px;
  left: 18px;
  display: flex;
  align-items: center;
  gap: 6px;
  z-index: 10;
}
.lc-status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #22c55e;
  display: inline-block;
  animation: lc-pulse 2s ease-in-out infinite;
}
.lc-status-text {
  font-size: 11px;
  color: var(--text-muted);
  letter-spacing: 0.02em;
}
@keyframes lc-pulse {
  0%, 100% { opacity: 1; box-shadow: 0 0 0 0 rgba(34,197,94,.5); }
  50% { opacity: .85; box-shadow: 0 0 0 4px rgba(34,197,94,0); }
}

/* Messages */
.lc-messages {
  flex: 1;
  overflow-y: auto;
  padding: 28px 28px 8px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  scrollbar-width: thin;
  scrollbar-color: transparent transparent;
}
.lc-messages:hover { scrollbar-color: rgba(100,116,139,.35) transparent; }

.lc-intro {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 24px 20px 16px;
}
.lc-intro-title {
  font-size: 24px;
  font-weight: 700;
  letter-spacing: -0.03em;
  color: var(--text-primary);
  margin: 0 0 8px;
}
.lc-intro-sub { color: var(--text-secondary); font-size: 14px; margin: 0; max-width: 440px; }

/* Bubbles */
.lc-msg { display: flex; flex-direction: column; }
.lc-user { align-items: flex-end; }
.lc-ai   { align-items: flex-start; }

.lc-bubble {
  max-width: 88%;
  padding: 10px 14px;
  border-radius: 18px;
  font-size: 13.5px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}
.lc-user .lc-bubble {
  background: var(--bg-active);
  color: var(--text-inverse);
  border-bottom-right-radius: 5px;
}
.lc-ai .lc-bubble {
  background: var(--bg-subtle);
  border: 1px solid var(--border);
  color: var(--text-primary);
  border-bottom-left-radius: 5px;
}
.lc-streaming { opacity: .92; }

/* Typing dots */
.lc-typing { display: flex; gap: 5px; align-items: center; padding: 14px 18px !important; }
.lc-typing span {
  width: 7px; height: 7px; border-radius: 50%;
  background: var(--text-muted);
  animation: lcbounce 1.2s infinite;
}
.lc-typing span:nth-child(2) { animation-delay: .2s; }
.lc-typing span:nth-child(3) { animation-delay: .4s; }
@keyframes lcbounce {
  0%,80%,100% { transform: translateY(0); opacity: .5; }
  40% { transform: translateY(-6px); opacity: 1; }
}

@media (max-width: 768px) {
  .lc-messages {
    padding: 18px 16px 6px;
    gap: 10px;
  }
  .lc-intro {
    padding: 40px 14px 12px;
  }
  .lc-intro-title {
    font-size: 20px;
    line-height: 1.25;
  }
  .lc-intro-sub {
    font-size: 13px;
    line-height: 1.5;
  }
  .lc-input-idle {
    transform: translateY(-18px);
    max-width: calc(100% + 56px);
    width: calc(100% + 56px);
    margin-left: -28px;
    padding: 8px 8px 16px;
  }
  .lc-input-active {
    padding: 8px 8px 16px;
  }
  .lc-suggestions {
    justify-content: center;
    flex-wrap: wrap;
    gap: 5px;
    padding-bottom: 4px;
    width: 100%;
  }
  .lc-chip {
    font-size: 9.5px;
    line-height: 1.2;
    padding: 6px 7px;
    white-space: nowrap;
    flex: 0 0 auto;
    max-width: none;
    border-radius: 999px;
  }
  .lc-ta-idle {
    height: 88px;
    padding-top: 16px;
  }
}

/* Limit banner */
.lc-limit {
  margin: 12px 20px 16px;
  padding: 22px 24px;
  border-radius: 20px;
  background: var(--accent-soft);
  border: 1.5px solid var(--border-active);
  text-align: center;
  animation: lc-fadein .3s ease;
}
@keyframes lc-fadein { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: none; } }
.lc-limit-icon { font-size: 28px; margin-bottom: 10px; }
.lc-limit p { margin: 0 0 16px; font-size: 14px; line-height: 1.6; color: var(--text-primary); }
.lc-limit-btns { display: flex; gap: 10px; justify-content: center; flex-wrap: wrap; }

/* Input area */
.lc-input-area {
  padding: 8px 20px 20px;
  transition: transform .35s cubic-bezier(.4,0,.2,1), max-width .35s cubic-bezier(.4,0,.2,1), margin .35s cubic-bezier(.4,0,.2,1);
}
.lc-input-idle   { transform: translateY(-72px); max-width: 70%; margin: 0 auto; }
.lc-input-active { transform: translateY(0); max-width: 100%; margin: 0; }

/* Suggestions */
.lc-suggestions { display: flex; flex-wrap: wrap; gap: 7px; margin-bottom: 12px; justify-content: center; }
.lc-chip {
  padding: 6px 12px;
  border-radius: 999px;
  border: 1px solid var(--border);
  background: var(--bg-subtle);
  color: var(--text-secondary);
  font: inherit;
  font-size: 12px;
  cursor: pointer;
  transition: all .15s;
  text-align: left;
}
.lc-chip:hover { background: var(--bg-hover); color: var(--text-primary); border-color: var(--accent); }

/* Input row */
.lc-row { display: flex; gap: 10px; align-items: flex-end; }

.lc-textarea {
  flex: 1;
  border: 1px solid var(--border-input);
  border-radius: 18px;
  padding: 12px 16px;
  background: var(--bg-input);
  color: var(--text-primary);
  font: inherit;
  font-size: 14px;
  resize: none;
  outline: none;
  line-height: 1.5;
  transition: height .35s cubic-bezier(.4,0,.2,1), border-color .15s;
}
.lc-ta-idle   { height: 120px; padding-top: 40px; }
.lc-ta-active { height: 44px; }
.lc-textarea:focus { border-color: var(--border-input-focus); box-shadow: 0 0 0 4px rgba(37,99,235,.08); }
.lc-textarea:disabled { opacity: .6; cursor: not-allowed; }

.lc-send {
  width: 44px; height: 44px; min-width: 44px;
  border-radius: 14px; border: none;
  background: var(--bg-active); color: var(--text-inverse);
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; transition: all .15s;
}
.lc-send:hover:not(:disabled) { filter: brightness(1.15); }
.lc-send:disabled { opacity: .35; cursor: not-allowed; }

.lc-counter { margin: 6px 4px 0; font-size: 12px; color: var(--text-muted); }
.lc-counter a { color: var(--accent); }
.lc-error {
  margin: 0 0 8px; padding: 8px 12px; border-radius: 12px;
  background: var(--error-bg); border: 1px solid var(--error-border);
  color: var(--error-text); font-size: 13px;
}
</style>
