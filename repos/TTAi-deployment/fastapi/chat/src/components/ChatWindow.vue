<script setup>
import { ref, watch, nextTick, onMounted } from 'vue'
import MessageBubble from './MessageBubble.vue'
import { sendMessage, createConversation } from '../lib/chatApi'
import { useRouter } from 'vue-router'
import { useVoice } from '../composables/useVoice'

const props = defineProps({
  convId: { type: String, default: null },
  messages: { type: Array, default: () => [] },
  model: { type: String, default: 'qwen3:4b' },
  models: { type: Array, default: () => [] },
  user: { type: Object, default: null },
  guestRemaining: { type: Number, default: 10 },
})
const emit = defineEmits(['conversation-created', 'conv-updated'])
const router = useRouter()

const localMessages = ref([...props.messages])
const streaming = ref(false)
const streamingContent = ref('')
const streamingStatus = ref('')
const streamingSources = ref([])
const input = ref('')
const inputEl = ref(null)
const messagesEl = ref(null)
const selectedModel = ref(props.model)
const error = ref('')
const replyTo = ref(null) // { role, content } of message being replied to

const { isListening, isSpeaking, ttsEnabled, sttSupported, ttsSupported, toggleListening, speak, stopSpeaking } = useVoice()

function handleMic() {
  toggleListening((transcript, isFinal) => {
    input.value = transcript
    if (isFinal) nextTick(autoResize)
  })
}

watch(() => props.messages, (msgs) => {
  if (streaming.value) return  // don't reset while a stream is in flight
  localMessages.value = [...msgs]
  scrollToBottom()
}, { deep: true })

watch(() => props.model, (m) => { selectedModel.value = m })

const SUGGESTIONS = [
  '✍️ Write a Python function to parse JSON',
  '🔍 Explain RAG in simple terms',
  '🐛 Help me debug this error',
  '📝 Summarize this text for me',
]

function autoResize() {
  if (!inputEl.value) return
  inputEl.value.style.height = 'auto'
  inputEl.value.style.height = Math.min(inputEl.value.scrollHeight, 200) + 'px'
}

function scrollToBottom() {
  nextTick(() => {
    if (messagesEl.value) messagesEl.value.scrollTop = messagesEl.value.scrollHeight
  })
}

async function submit(text) {
  if (isListening.value) stopListening()
  let content = (text || input.value).trim()
  if (!content || streaming.value) return
  error.value = ''

  // Prepend reply quote to content if replying
  if (replyTo.value) {
    const quotedSender = replyTo.value.role === 'user' ? 'You' : 'Trợ lý Tuệ Tuệ'
    const quotedText = replyTo.value.content.slice(0, 200)
    content = `[Replying to ${quotedSender}: "${quotedText}"]\n\n${content}`
    replyTo.value = null
  }

  input.value = ''
  nextTick(autoResize)

  // Show user message immediately — before async createConversation
  localMessages.value.push({ id: Date.now(), role: 'user', content })
  streaming.value = true
  streamingContent.value = ''
  scrollToBottom()

  streamingStatus.value = ''
  streamingSources.value = []

  let convId = props.convId
  if (!convId || convId === 'new') {
    try {
      const res = await createConversation(selectedModel.value)
      convId = res.id
      emit('conversation-created', convId)
      router.replace(`/c/${convId}`)
    } catch (e) {
      localMessages.value.pop()
      streaming.value = false
      error.value = e.message
      return
    }
  }

  try {
    for await (const chunk of sendMessage(convId, content, selectedModel.value)) {
      if (chunk.type === 'content') {
        streamingStatus.value = ''
        streamingContent.value += chunk.content
        scrollToBottom()
      } else if (chunk.type === 'status') {
        streamingStatus.value = chunk.content
        scrollToBottom()
      } else if (chunk.type === 'sources') {
        streamingSources.value = chunk.sources || []
        streamingStatus.value = ''
      } else if (chunk.type === 'done') {
        const finalContent = streamingContent.value
        localMessages.value.push({
          id: chunk.message_id,
          role: 'assistant',
          content: finalContent,
          sources: streamingSources.value.length ? [...streamingSources.value] : undefined,
        })
        streamingContent.value = ''
        streamingStatus.value = ''
        streamingSources.value = []
        speak(finalContent)
        emit('conv-updated', convId)
      } else if (chunk.type === 'error') {
        error.value = chunk.content
      }
    }
  } catch (e) {
    error.value = e.message || 'Connection error. Please try again.'
    if (streamingContent.value) {
      localMessages.value.push({ id: Date.now(), role: 'assistant', content: streamingContent.value })
      streamingContent.value = ''
    }
  } finally {
    streaming.value = false
    streamingStatus.value = ''
    streamingSources.value = []
    scrollToBottom()
  }
}

function onKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    submit()
  }
  if (e.key === 'Escape' && replyTo.value) {
    replyTo.value = null
  }
}

function handleReply(msgData) {
  replyTo.value = msgData
  nextTick(() => inputEl.value?.focus())
}

onMounted(() => {
  inputEl.value?.focus()
  scrollToBottom()
})

// Parse reply-to context from stored messages (messages saved with "[Replying to...]" prefix)
function getReplyTo(msg) {
  if (!msg.content.startsWith('[Replying to ')) return null
  const match = msg.content.match(/^\[Replying to (You|Trợ lý Tuệ Tuệ): "(.+?)"\]/)
  if (!match) return null
  return { role: match[1] === 'You' ? 'user' : 'assistant', content: match[2] }
}

function getDisplayContent(msg) {
  if (!msg.content.startsWith('[Replying to ')) return msg.content
  const idx = msg.content.indexOf(']\n\n')
  return idx > -1 ? msg.content.slice(idx + 3) : msg.content
}
</script>

<template>
  <div style="flex: 1; display: flex; flex-direction: column; min-height: 0;">

    <!-- Messages -->
    <div class="messages-area" ref="messagesEl">
      <!-- Empty state -->
      <div v-if="!localMessages.length && !streaming" style="height: 100%; display: flex; align-items: center; justify-content: center;">
        <div class="empty-state">
          <img :src="'/chat/logo.jpg'" alt="Tuệ Tuệ Ai" class="empty-logo-img" />
          <div class="empty-title">Tuệ Tuệ Ai có thể giúp gì cho bạn?</div>
          <div class="empty-subtitle">
            Ask anything — code, analysis, writing, math, and more.
            <span v-if="!user"> Sign in for memory &amp; unlimited chats.</span>
          </div>
          <div class="suggestion-grid">
            <button
              v-for="s in SUGGESTIONS"
              :key="s"
              class="suggestion-chip"
              @click="submit(s.replace(/^[\w\W]{2} /, ''))"
            >{{ s }}</button>
          </div>
        </div>
      </div>

      <!-- Message list -->
      <div class="messages-inner" v-else>
        <MessageBubble
          v-for="msg in localMessages"
          :key="msg.id"
          :role="msg.role"
          :content="getDisplayContent(msg)"
          :reply-to="getReplyTo(msg)"
          :message-id="msg.role === 'assistant' ? String(msg.id) : null"
          :sources="msg.sources || []"
          @reply="handleReply"
        />
        <!-- Streaming -->
        <MessageBubble
          v-if="streaming || streamingContent || streamingStatus"
          role="assistant"
          :content="streamingContent"
          :streaming="streaming"
          :search-status="streamingStatus"
          :sources="streamingSources"
        />
      </div>
    </div>

    <!-- Input -->
    <div class="input-area">
      <div class="input-inner">

        <!-- Guest banner -->
        <div v-if="!user && guestRemaining <= 3" class="guest-banner">
          <span>⚡</span>
          <span>
            {{ guestRemaining }} messages left.
            <a href="#" @click.prevent="$router.push('/login')">Sign in</a> or
            <a href="https://console.tuetue.vn/signup" target="_blank">create account</a>
            for unlimited access.
          </span>
        </div>

        <!-- Reply preview -->
        <div v-if="replyTo" class="reply-preview">
          <div class="reply-preview-content">
            <strong>↩ Replying to {{ replyTo.role === 'user' ? 'You' : 'Trợ lý Tuệ Tuệ' }}</strong>
            <span>{{ replyTo.content.slice(0, 160) }}{{ replyTo.content.length > 160 ? '…' : '' }}</span>
          </div>
          <button class="reply-cancel" @click="replyTo = null" title="Cancel reply">✕</button>
        </div>

        <p v-if="error" style="color: #ef4444; font-size: 13px; margin-bottom: 8px;">{{ error }}</p>

        <div class="input-box">
          <textarea
            ref="inputEl"
            class="input-textarea"
            v-model="input"
            :placeholder="isListening ? '🎤 Đang nghe…' : replyTo ? 'Viết câu trả lời…' : 'Hãy hỏi trợ lý Tuệ Tuệ của bạn…'"
            rows="1"
            @input="autoResize"
            @keydown="onKeydown"
          />
          <!-- Mic button -->
          <button
            v-if="sttSupported"
            class="mic-btn"
            :class="{ listening: isListening }"
            @click="handleMic"
            :title="isListening ? 'Dừng ghi âm' : 'Nhập bằng giọng nói (vi-VN)'"
          >
            <svg v-if="!isListening" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="9" y="2" width="6" height="11" rx="3"/>
              <path d="M5 10a7 7 0 0 0 14 0"/><line x1="12" y1="19" x2="12" y2="22"/><line x1="8" y1="22" x2="16" y2="22"/>
            </svg>
            <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <rect x="6" y="6" width="12" height="12" rx="2"/>
            </svg>
          </button>
          <button
            class="send-btn"
            :disabled="!input.trim() || streaming"
            @click="submit()"
            title="Send (Enter)"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <line x1="22" y1="2" x2="11" y2="13"/>
              <polygon points="22 2 15 22 11 13 2 9 22 2"/>
            </svg>
          </button>
        </div>

        <!-- Footer -->
        <div class="input-footer">
          <span style="font-size:11px; color:var(--muted);">
            Copyright 2026 ©
            <a href="https://minhtue.vn" target="_blank" rel="noopener" style="color:var(--muted); text-decoration:underline; text-underline-offset:2px;">Minh Tue Trading Investment JSC</a>.
          </span>
          <div style="display:flex; align-items:center; gap:10px;">
            <!-- TTS toggle -->
            <button
              v-if="ttsSupported"
              @click="ttsEnabled = !ttsEnabled; isSpeaking && stopSpeaking()"
              :title="ttsEnabled ? 'Tắt đọc to' : 'Bật đọc to'"
              style="background:none; border:none; cursor:pointer; padding:0; font-size:13px; line-height:1; color:var(--muted); opacity: ttsEnabled ? 1 : 0.4;"
              :style="{ opacity: ttsEnabled ? 1 : 0.35 }"
            >{{ isSpeaking ? '🔊' : '🔈' }}</button>
            <span class="input-hint">Enter to send · Shift+Enter for new line · Esc to cancel reply</span>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>
