/**
 * Reapply i18n $t() calls to all .vue templates.
 * Reads en.json keys, finds matching English text in template,
 * and replaces with $t('componentName.keyName')
 */

const fs = require('fs');
const path = require('path');

const localeDir = 'C:/Users/vannt-pc/.openclaw/workspace/repos/TTAi-deployment/fastapi/portal/src/i18n/locales';
const srcDir = 'C:/Users/vannt-pc/.openclaw/workspace/repos/TTAi-deployment/fastapi/portal/src';

// Load en.json
const en = JSON.parse(fs.readFileSync(path.join(localeDir, 'en.json'), 'utf-8'));

// Build reverse map: text -> { component, key }
const textToKey = {};
Object.entries(en).forEach(([component, keys]) => {
  Object.entries(keys).forEach(([key, value]) => {
    const trimmed = value.trim();
    if (trimmed.length > 2) {
      const normalized = trimmed
        .replace(/\s+/g, ' ')
        .replace(/&amp;/g, '&')
        .replace(/&lt;/g, '<')
        .replace(/&gt;/g, '>');
      textToKey[normalized] = { component, key };
    }
  });
});

function processVueFile(filePath) {
  let content = fs.readFileSync(filePath, 'utf-8');
  let original = content;
  let replacements = 0;

  // Extract the <template> section
  const templateMatch = content.match(/<template>([\s\S]*?)<\/template>/);
  if (!templateMatch) return false;

  let template = templateMatch[1];
  let newTemplate = template;

  // Find Vue text interpolation areas: {{ text }} or between HTML tags
  // Strategy: find English text nodes in template, replace
  const textPatterns = [
    // Between tags: >Text here<
    />(?!\s*(?:&nbsp;|\s)*<)([A-Z][A-Za-z0-9\s,.'!?\-&/()[\]{}]{3,100})</g,
  ];

  const found = [];
  let m;
  while ((m = textPatterns[0].exec(template)) !== null) {
    const text = m[1].trim();
    if (text.length < 3) continue;
    // Skip Vue directives, props, CSS classes, HTML tags
    if (text.startsWith(':') || text.startsWith('@') || text.startsWith('v-') || text.startsWith('#')) continue;
    if (text.startsWith('import ') || text.startsWith('export ')) continue;
    if (text.startsWith('http') || text.startsWith('https://')) continue;
    if (text.includes('{{')) continue;

    const normalized = text.replace(/\s+/g, ' ').replace(/&amp;/g, '&');
    if (textToKey[normalized]) {
      found.push({ index: m.index, original: m[0], text, fullMatch: m[0] });
    }
  }

  // Sort by index descending to replace safely
  found.sort((a, b) => b.index - a.index);
  for (const item of found) {
    const { component, key } = textToKey[item.text.replace(/\s+/g, ' ').replace(/&amp;/g, '&')];
    const replacement = item.fullMatch.replace(item.text, `{{ \$t('${component}.${key}') }}`);
    newTemplate = newTemplate.substring(0, item.index) + replacement + newTemplate.substring(item.index + item.fullMatch.length);
    replacements++;
  }

  if (replacements > 0) {
    content = content.replace(template, newTemplate);
    fs.writeFileSync(filePath, content, 'utf-8');
  }

  return replacements;
}

// Process all .vue files
const pages = fs.readdirSync(path.join(srcDir, 'pages')).filter(f => f.endsWith('.vue'));
const components = fs.readdirSync(path.join(srcDir, 'components')).filter(f => f.endsWith('.vue'));
const allFiles = [
  ...pages.map(f => path.join(srcDir, 'pages', f)),
  ...components.map(f => path.join(srcDir, 'components', f)),
  path.join(srcDir, 'App.vue')
];

let total = 0;
allFiles.forEach(f => {
  const r = processVueFile(f);
  if (r > 0) {
    console.log(`✅ ${path.basename(f)}: ${r} replacements`);
    total += r;
  }
});
console.log(`\nTotal: ${total} replacements across ${allFiles.length} files`);
