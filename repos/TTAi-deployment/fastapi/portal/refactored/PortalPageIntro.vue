<script setup>
defineProps({
  eyebrow: { type: String, required: true },
  title: { type: String, required: true },
  description: { type: String, required: true },
})
</script>

<template>
  <section class="page-intro">
    <div class="eyebrow">{{ eyebrow }}</div>
    <h2 class="page-title">{{ title }}</h2>
    <p class="page-description">{{ description }}</p>
  </section>
</template>
