/**
 * translate-locales-v2.js - Batch translate en.json => 5 locales
 * 
 * Strategy: 
 * - en.json has 22 component keys (34KB total)
 * - We spawn 5 subagents (one per language) 
 * - Each subagent reads en.json => produces its locale JSON
 * - We write the JSON file
 */

import { readFileSync, writeFileSync } from 'fs'
import { execSync } from 'child_process'

const enPath = 'C:/Users/vannt-pc/.openclaw/workspace/repos/TTAi-deployment/fastapi/portal/src/i18n/locales/en.json'
const localeDir = 'C:/Users/vannt-pc/.openclaw/workspace/repos/TTAi-deployment/fastapi/portal/src/i18n/locales'

const en = JSON.parse(readFileSync(enPath, 'utf-8'))

const TARGETS = ['vi', 'fr', 'zh', 'ko', 'ja']
const CMD = 'openclaw sessions spawn'  // not used; we'll use direct API call

// We'll translate by sending each batch via sessions_spawn or via exec openclaw
// For now, save the batches as files
const batches = {}
for (const [key, val] of Object.entries(en)) {
  // Group: small components together, large ones alone
  const s = JSON.stringify(val).length
  if (s > 3000) {
    batches[key] = val
  }
}

// Write batch files for manual processing
let batchNum = 1
let currentBatch = {}

for (const [key, val] of Object.entries(en)) {
  const jsonLen = JSON.stringify(val).length
  const currentLen = JSON.stringify(currentBatch).length
  
  if (currentLen + jsonLen > 3000 && Object.keys(currentBatch).length > 0) {
    // Flush batch
    writeFileSync(`${localeDir}/batch-${batchNum}.json`, JSON.stringify(currentBatch))
    console.log(`Wrote batch-${batchNum}.json (${JSON.stringify(currentBatch).length} chars, ${Object.keys(currentBatch).length} components)`)
    batchNum++
    currentBatch = {}
  }
  
  currentBatch[key] = val
}

if (Object.keys(currentBatch).length > 0) {
  writeFileSync(`${localeDir}/batch-${batchNum}.json`, JSON.stringify(currentBatch))
  console.log(`Wrote batch-${batchNum}.json (${JSON.stringify(currentBatch).length} chars, ${Object.keys(currentBatch).length} components)`)
}

console.log(`Total batches: ${batchNum}`)
