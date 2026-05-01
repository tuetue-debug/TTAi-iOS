/**
 * translate-batch.cjs - Read en.json, splits into batches,
 * calls OpenClaw sessions_spawn for each batch per language.
 * 
 * Strategy:
 * - en.json has 22 component keys (~34KB)
 * - Split into 6 batches (~5-6KB each)
 * - For each batch, for each of 5 languages, generate translation
 * - We use direct HTTP POST to OpenClaw API (or sessions_spawn)
 */

const fs = require('fs');
const path = require('path');
const en = JSON.parse(fs.readFileSync(
  'C:/Users/vannt-pc/.openclaw/workspace/repos/TTAi-deployment/fastapi/portal/src/i18n/locales/en.json',
  'utf-8'
));

// Split into batches by size (~5KB each)
const entries = Object.entries(en);
const batches = [];
let currentBatch = {};
let currentSize = 0;

for (const [key, value] of entries) {
  const jsonLen = JSON.stringify(value).length;
  if (currentSize + jsonLen > 5000 && Object.keys(currentBatch).length > 0) {
    batches.push({ ...currentBatch });
    currentBatch = {};
    currentSize = 0;
  }
  currentBatch[key] = value;
  currentSize += jsonLen;
}
if (Object.keys(currentBatch).length > 0) batches.push(currentBatch);

console.log(`Total: ${entries.length} components in ${batches.length} batches`);
batches.forEach((b, i) => {
  console.log(`  Batch ${i}: ${Object.keys(b).length} components, ${JSON.stringify(b).length} bytes`);
});

// Output instruction for manual spawning
const localeDir = 'C:/Users/vannt-pc/.openclaw/workspace/repos/TTAi-deployment/fastapi/portal/src/i18n/locales';

batches.forEach((batch, idx) => {
  const filePath = path.join(localeDir, `batch-${idx}.json`);
  fs.writeFileSync(filePath, JSON.stringify(batch, null, 2), 'utf-8');
  console.log(`Written: batch-${idx}.json`);
});

console.log('\nTo translate, spawn subagents with:');
console.log('Read C:/Users/vannt-pc/.openclaw/workspace/repos/TTAi-deployment/fastapi/portal/src/i18n/locales/en.json');
console.log('Read all batch-0.json through batch-5.json');
console.log('For each language (vi, fr, zh, ko, ja), translate all 6 batches and combine into one locale file.');
