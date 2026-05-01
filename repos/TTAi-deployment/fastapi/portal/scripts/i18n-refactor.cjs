/**
 * i18n Auto-Refactor Script
 * 
 * Reads all .vue files, replaces hardcoded text with $t() calls,
 * generates EN locale JSON, and prepares for batch translation.
 * 
 * Usage: node scripts/i18n-refactor.js
 */

const fs = require('fs')
const path = require('path')

const SRC_DIR = path.resolve(__dirname, '../src')
const PAGES_DIR = path.join(SRC_DIR, 'pages')
const COMPONENTS_DIR = path.join(SRC_DIR, 'components')
const LOCALE_DIR = path.join(SRC_DIR, 'i18n/locales')

// Files already done or should be skipped
const SKIP_FILES = ['TopNav.vue', 'App.vue']

// Map for generated keys
const localeMap = {} // Component -> { key: englishText }

// Regex to find hardcoded text in templates:
// 1. >some text< (text nodes)
// 2. v-text="text" -> v-text="$t('key')"
// 3. placeholder="text" -> :placeholder="$t('key')"
// 3. title="text" -> :title="$t('key')"
// 4. alt="text" -> :alt="$t('key')"
// 5. aria-label="text" -> :aria-label="$t('key')"

function toCamelCase(str) {
  return str
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+(.)?/g, (_, c) => c ? c.toUpperCase() : '')
    .replace(/^(.)/, c => c.toLowerCase())
    .substring(0, 60) // limit length
}

function sanitizeKey(text) {
  let key = text
    .trim()
    .replace(/<[^>]+>/g, '')     // remove HTML tags
    .replace(/&[a-z]+;/g, '')    // remove HTML entities
    .replace(/[^a-zA-Z0-9 ]/g, '') // keep only alphanumeric + space
    .trim()
  
  // Take first few meaningful words
  const words = key.split(/\s+/).filter(w => w.length > 1)
  key = words.slice(0, 5).join('.')
  if (!key) key = 'text'
  return toCamelCase(key)
}

const SKIP_TEXT_PATTERNS = [
  /^\{\{/,
  /^\$t\(/,
  /^[0-9\.\,\s\%\$\(\)]+$/,
  /^\s*$/,
  /^-{2,}/,
  /^&nbsp/,
  /^!--/,
  /^[a-z\-_]+$/, // class names, directives
  /^@/,
  /^v-/,
  /^router-/,
  /^ref="/,
  /^:/,
]

function isSkippable(text) {
  const trimmed = text.trim()
  if (trimmed.length < 3) return true
  if (trimmed.length > 200) return true
  for (const p of SKIP_TEXT_PATTERNS) {
    if (p.test(trimmed)) return true
  }
  return false
}

function collectTexts(content) {
  const texts = []
  
  // Text between > and <
  const textRegex = />([^<]+)</g
  let match
  while ((match = textRegex.exec(content)) !== null) {
    const text = match[1].trim()
    if (!isSkippable(text)) {
      texts.push({
        text,
        index: match.index,
        length: match[0].length,
        type: 'text-node'
      })
    }
  }
  
  // v-text attributes
  const vTextRegex = /(\bv-text\s*=\s*)"([^"]+)"(?!.*\$t)/g
  while ((match = vTextRegex.exec(content)) !== null) {
    const text = match[2].trim()
    if (!isSkippable(text)) {
      texts.push({
        text,
        index: match.index,
        length: match[0].length,
        type: 'v-text',
        attrStart: match.index + match[1].length,
        attrEnd: match.index + match[0].length
      })
    }
  }
  
  // :label, placeholder, title, alt attributes (that aren't already $t())
  const attrRegex = /((?::label|placeholder|title|alt|aria-label)\s*=\s*)"([^"{}]+)"/g
  while ((match = attrRegex.exec(content)) !== null) {
    const text = match[2].trim()
    if (!isSkippable(text) && !text.startsWith('{{')) {
      texts.push({
        text,
        index: match.index,
        length: match[0].length,
        type: 'attr',
        attrName: match[1],
        attrStart: match.index + match[1].length,
        attrEnd: match.index + match[0].length
      })
    }
  }
  
  return texts
}

function generateKey(componentName, text, existingKeys) {
  let key = sanitizeKey(text)
  if (!key) key = 'text'
  
  // Ensure uniqueness
  let finalKey = key
  let counter = 1
  while (existingKeys.has(finalKey)) {
    finalKey = `${key}_${counter}`
    counter++
  }
  existingKeys.add(finalKey)
  
  return finalKey
}

function getComponentShortName(filename) {
  // FeaturesPage -> Features
  // AuthCard -> AuthCard
  // PortalQuickActions -> QuickActions
  return filename.replace(/\.vue$/, '')
}

// Main refactor function
function refactorFile(filePath) {
  const filename = path.basename(filePath)
  if (SKIP_FILES.includes(filename)) return null
  
  const componentName = getComponentShortName(filename)
  const content = fs.readFileSync(filePath, 'utf-8')
  
  // Skip files with no template
  if (!content.includes('<template')) return null
  
  const texts = collectTexts(content)
  if (texts.length === 0) return null
  
  console.log(`\n${filename}: ${texts.length} texts found`)
  
  // Build locale entries
  if (!localeMap[componentName]) localeMap[componentName] = {}
  
  const existingKeys = new Set(Object.keys(localeMap[componentName]))
  
  // Process each text in reverse order to maintain indices
  const replacements = []
  
  for (const t of texts) {
    const key = generateKey(componentName, t.text, existingKeys)
    localeMap[componentName][key] = t.text
    
    if (t.type === 'text-node') {
      replacements.push({
        index: t.index,
        length: t.length,
        replacement: `>{{ $t('${componentName}.${key}') }}<`
      })
    } else if (t.type === 'v-text') {
      replacements.push({
        index: t.attrStart,
        length: (t.attrEnd - t.attrStart),
        replacement: `:${t.attrStart > 0 ? content.substring(0, t.attrStart).match(/[a-z\-]+$/) || 'v-text' : 'v-text'}=$t('${componentName}.${key}')` // simplified
      })
    }
  }
  
  // Sort replacements in reverse order
  replacements.sort((a, b) => b.index - a.index)
  
  // Apply replacements
  let newContent = content
  for (const r of replacements) {
    if (r.type === 'text-node') {
      newContent = newContent.substring(0, r.index) + r.replacement + newContent.substring(r.index + r.length)
    }
  }
  
  return { filename, componentName, content: newContent, count: texts.length }
}

// Process all files
const results = []

// Process pages
const pageFiles = fs.readdirSync(PAGES_DIR).filter(f => f.endsWith('.vue'))
for (const f of pageFiles) {
  const result = refactorFile(path.join(PAGES_DIR, f))
  if (result) results.push(result)
}

// Process components
const componentFiles = fs.readdirSync(COMPONENTS_DIR).filter(f => f.endsWith('.vue'))
for (const f of componentFiles) {
  const result = refactorFile(path.join(COMPONENTS_DIR, f))
  if (result) results.push(result)
}

console.log(`\n\n=== RESULTS ===`)
console.log(`Files processed: ${results.length}`)
console.log(`Total text strings: ${results.reduce((s, r) => s + r.count, 0)}`)

// Generate EN locale file
const enLocale = {}
const sortedComponents = Object.keys(localeMap).sort()
for (const comp of sortedComponents) {
  enLocale[comp] = localeMap[comp]
}

const localeDir = LOCALE_DIR
if (!fs.existsSync(localeDir)) {
  fs.mkdirSync(localeDir, { recursive: true })
}

fs.writeFileSync(
  path.join(localeDir, 'en.json'),
  JSON.stringify(enLocale, null, 2) + '\n',
  'utf-8'
)

console.log(`\n✅ en.json written: ${Object.keys(enLocale).length} components, ${Object.values(enLocale).reduce((s, c) => s + Object.keys(c).length, 0)} keys`)

// Generate refactored files
const outDir = path.resolve(__dirname, '../refactored')
if (!fs.existsSync(outDir)) {
  fs.mkdirSync(outDir)
}

for (const r of results) {
  fs.writeFileSync(path.join(outDir, r.filename), r.content, 'utf-8')
}

console.log(`✅ ${results.length} refactored files written to refactored/`)

// Write script to apply refactored files
const applyScript = `# Apply refactored files
$src = "refactored"
$pages = Join-Path $src "pages"
$components = Join-Path $src "components"

if (Test-Path $pages) { Copy-Item "$pages\\*" "src\\pages\\" -Force }
if (Test-Path $components) { Copy-Item "$components\\*" "src\\components\\" -Force }

Write-Host "Applied refactored files"
`

fs.writeFileSync(path.resolve(__dirname, '../apply-refactor.ps1'), applyScript, 'utf-8')
console.log(`✅ apply-refactor.ps1 written`)
