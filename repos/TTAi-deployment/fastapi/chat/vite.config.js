import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  base: '/chat/',
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    chunkSizeWarningLimit: 600,
    rollupOptions: {
      output: {
        manualChunks: {
          'vue-core': ['vue', 'vue-router'],
          'marked': ['marked'],
        },
      },
    },
  },
  server: {
    proxy: {
      '/chat-api': 'http://localhost:8000',
      '/auth': 'http://localhost:8000',
    },
  },
})
