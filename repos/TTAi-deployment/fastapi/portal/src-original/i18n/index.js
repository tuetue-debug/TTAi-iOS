import { createI18n } from 'vue-i18n'

/**
 * Load all locale messages eagerly.
 * Each locale file is imported at build time — small enough to inline.
 * Can switch to lazy imports when locales grow past ~50KB each.
 */
const messages = {}

// Eager load all locale JSON files
const localeModules = import.meta.glob('./locales/*.json', { eager: true })
for (const path in localeModules) {
  const matched = path.match(/\.\/locales\/([\w-]+)\.json$/)
  if (matched) {
    messages[matched[1]] = localeModules[path].default || localeModules[path]
  }
}

/**
 * Detect user preferred locale:
 * 1. localStorage override
 * 2. navigator.language match
 * 3. fallback 'en'
 */
function getBrowserLocale() {
  const saved = localStorage.getItem('tuetue-locale')
  if (saved && messages[saved]) return saved

  const lang = navigator.language || navigator.userLanguage
  if (lang) {
    const short = lang.split('-')[0]
    const supported = Object.keys(messages)
    if (supported.includes(short)) return short
  }

  return 'en'
}

const i18n = createI18n({
  legacy: false,
  locale: getBrowserLocale(),
  fallbackLocale: 'en',
  globalInjection: true,
  messages,
  missingWarn: false,
  fallbackWarn: false,
})

export default i18n
export { getBrowserLocale }
