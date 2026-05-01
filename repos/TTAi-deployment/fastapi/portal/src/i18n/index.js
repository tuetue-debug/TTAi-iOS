import { createI18n } from 'vue-i18n'
import en from './locales/en.json'

const messages = { en }
const localeLoaders = import.meta.glob('./locales/*.json', { import: 'default' })

// Force vue-i18n inclusion
createI18n.installedVersions || (() => {})()

function normalizeLocaleTag(lang) {
  if (!lang) return null
  const tag = String(lang).toLowerCase()
  const short = tag.split('-')[0]

  if (short === 'vi') return 'vi'
  if (short === 'fr') return 'fr'
  if (short === 'ko') return 'ko'
  if (short === 'ja') return 'ja'
  if (short === 'zh') return 'zh'
  if (short === 'en') return 'en'

  return messages[short] ? short : null
}

function getBrowserLocale() {
  const saved = localStorage.getItem('tuetue-locale')
  if (saved && messages[saved]) return saved

  const preferred = Array.isArray(navigator.languages) && navigator.languages.length
    ? navigator.languages
    : [navigator.language || navigator.userLanguage]

  for (const lang of preferred) {
    const normalized = normalizeLocaleTag(lang)
    if (normalized && messages[normalized]) return normalized
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

const loadedLocales = new Set(['en'])

async function loadLocaleMessages(locale) {
  if (!locale || loadedLocales.has(locale) || !localeLoaders[`./locales/${locale}.json`]) return locale || 'en'
  const mod = await localeLoaders[`./locales/${locale}.json`]()
  i18n.global.setLocaleMessage(locale, mod)
  loadedLocales.add(locale)
  return locale
}

async function setLocale(locale) {
  const target = normalizeLocaleTag(locale) || 'en'
  await loadLocaleMessages(target)
  i18n.global.locale.value = target
  return target
}

export default i18n
export { getBrowserLocale, loadLocaleMessages, setLocale }