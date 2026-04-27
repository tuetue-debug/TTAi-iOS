import { ref } from 'vue'

const theme = ref('light')

function getInitialTheme() {
  const stored = localStorage.getItem('tuetue-theme')
  if (stored) return stored
  if (window.matchMedia('(prefers-color-scheme: dark)').matches) return 'dark'
  return 'light'
}

function applyTheme(val) {
  document.documentElement.className = val === 'dark' ? 'theme-dark' : ''
  const meta = document.querySelector('meta[name=theme-color]')
  if (meta) meta.content = val === 'dark' ? '#0f172a' : '#f6f7fb'
  theme.value = val
  localStorage.setItem('tuetue-theme', val)
}

function toggleTheme() {
  applyTheme(theme.value === 'dark' ? 'light' : 'dark')
}

function initTheme() {
  applyTheme(getInitialTheme())
}

export function useTheme() {
  return { theme, toggleTheme, initTheme }
}
