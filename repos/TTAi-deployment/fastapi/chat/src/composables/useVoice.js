import { ref, onUnmounted } from 'vue'

const SR = window.SpeechRecognition || window.webkitSpeechRecognition

// ── Singleton state (shared across all useVoice() calls) ──────────────────────
const ttsEnabled  = ref(false)
const isSpeaking  = ref(false)
const isListening = ref(false)

// ── Voice loader (fix Chrome "getVoices() = []" bug) ─────────────────────────
function loadVoice() {
  return new Promise(resolve => {
    const pick = () => {
      const all = window.speechSynthesis.getVoices()
      resolve(all.find(v => v.lang.startsWith('vi')) || all[0] || null)
    }
    const voices = window.speechSynthesis.getVoices()
    if (voices.length) { pick(); return }
    window.speechSynthesis.addEventListener('voiceschanged', pick, { once: true })
  })
}

export function useVoice() {
  const sttSupported = !!SR
  const ttsSupported = !!window.speechSynthesis

  // ── STT ──────────────────────────────────────────────────────────────────────
  let recognition = null
  if (SR) {
    recognition = new SR()
    recognition.lang = 'vi-VN'
    recognition.continuous = false
    recognition.interimResults = true
  }

  function startListening(onTranscript) {
    if (!recognition || isListening.value) return
    isListening.value = true
    recognition.onresult = (e) => {
      const transcript = Array.from(e.results).map(r => r[0].transcript).join('')
      const isFinal = e.results[e.results.length - 1].isFinal
      onTranscript(transcript, isFinal)
    }
    recognition.onend  = () => { isListening.value = false }
    recognition.onerror = () => { isListening.value = false }
    recognition.start()
  }

  function stopListening() {
    recognition?.stop()
    isListening.value = false
  }

  function toggleListening(onTranscript) {
    isListening.value ? stopListening() : startListening(onTranscript)
  }

  // ── TTS ──────────────────────────────────────────────────────────────────────
  async function speak(text) {
    if (!ttsEnabled.value || !window.speechSynthesis) return
    const clean = text.replace(/[*_`#>~\[\]()]/g, '').replace(/\n+/g, ' ').trim()
    if (!clean) return

    window.speechSynthesis.cancel()
    const utt = new SpeechSynthesisUtterance(clean)
    const voice = await loadVoice()
    if (voice) utt.voice = voice
    utt.lang = voice?.lang || 'vi-VN'
    utt.rate = 1.05
    utt.onstart = () => { isSpeaking.value = true }
    utt.onend   = () => { isSpeaking.value = false }
    utt.onerror = () => { isSpeaking.value = false }
    window.speechSynthesis.speak(utt)
  }

  function stopSpeaking() {
    window.speechSynthesis?.cancel()
    isSpeaking.value = false
  }

  function toggleTts() {
    if (ttsEnabled.value && isSpeaking.value) stopSpeaking()
    ttsEnabled.value = !ttsEnabled.value
  }

  onUnmounted(() => { stopListening(); stopSpeaking() })

  return {
    isListening, isSpeaking, ttsEnabled,
    sttSupported, ttsSupported,
    toggleListening, stopListening,
    speak, stopSpeaking, toggleTts,
  }
}
