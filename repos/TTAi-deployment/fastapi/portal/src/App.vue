<template>
  <router-view />
</template>

<script setup>
import { onMounted } from 'vue'
import { getBrowserLocale, setLocale } from './i18n/index.js'

onMounted(async () => {
  const detected = getBrowserLocale()
  await setLocale(detected)
})
</script>
