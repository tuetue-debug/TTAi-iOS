<script setup>
import { ref } from 'vue'

const props = defineProps({
  text: { type: String, required: true },
  label: { type: String, default: 'Copy' },
})

const copied = ref(false)

async function handleCopy() {
  try {
    await navigator.clipboard.writeText(props.text)
    copied.value = true
    setTimeout(() => {
      copied.value = false
    }, 1600)
  } catch {
    copied.value = false
  }
}
</script>

<template>
  <button class="ghost-btn copy-btn" type="button" @click="handleCopy">
    {{ copied ? 'Copied' : label }}
  </button>
</template>
