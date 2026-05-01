import { ref } from 'vue'

const STORAGE_KEY = 'tuetue-theme'

function getStoredTheme() {
  const stored = localStorage.getItem(STORAGE_KEY)
  if (stored === 'dark' || stored === 'light') return stored
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

const theme = ref(getStoredTheme())

function applyTheme(val) {
  if (val === 'dark') {
    document.documentElement.classList.add('theme-dark')
    document.documentElement.classList.remove('theme-light')
  } else {
    document.documentElement.classList.remove('theme-dark')
    document.documentElement.classList.add('theme-light')
  }
  const meta = document.querySelector('meta[name=theme-color]')
  if (meta) meta.content = val === 'dark' ? '#0f172a' : '#f6f7fb'
}

applyTheme(theme.value)

// Tự động theo hệ thống khi chưa có preference thủ công
window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
  if (!localStorage.getItem(STORAGE_KEY)) {
    const next = e.matches ? 'dark' : 'light'
    theme.value = next
    applyTheme(next)
  }
})

function toggleTheme() {
  const next = theme.value === 'dark' ? 'light' : 'dark'
  theme.value = next
  applyTheme(next)
  localStorage.setItem(STORAGE_KEY, next) // lưu khi user chọn thủ công
}

export function useTheme() {
  return { theme, toggleTheme }
}
