<template>
  <router-view />
</template>

<script setup>
import { useI18n } from 'vue-i18n'
import { onMounted } from 'vue'
import { getBrowserLocale } from './i18n/index.js'

const { locale } = useI18n()

onMounted(() => {
  // Auto-detect locale on mount
  const detected = getBrowserLocale()
  if (detected !== locale.value) {
    locale.value = detected
  }
})
</script>
