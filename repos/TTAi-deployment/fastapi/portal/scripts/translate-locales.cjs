/**
 * i18n Translation Script
 * Translates EN locale into 5 languages using TTAi API
 * 
 * Usage: node scripts/translate-locales.cjs
 */

const fs = require('fs')
const path = require('path')
const https = require('https')
const http = require('http')

const LOCALE_DIR = path.resolve(__dirname, '../src/i18n/locales')
const API_URL = 'http://127.0.0.1:8325/v1/chat/completions'

// Read EN locale
const enPath = path.join(LOCALE_DIR, 'en.json')
const enData = JSON.parse(fs.readFileSync(enPath, 'utf-8'))

// Target languages
const TARGETS = [
  { code: 'vi', name: 'Vietnamese' },
  { code: 'fr', name: 'French' },
  { code: 'zh', name: 'Chinese (Simplified)' },
  { code: 'ko', name: 'Korean' },
  { code: 'ja', name: 'Japanese' },
]

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms))
}

function callAPI(messages) {
  return new Promise((resolve, reject) => {
    const data = JSON.stringify({
      model: 'gpt-mini',
      max_tokens: 8192,
      messages,
      temperature: 0.1,
      max_tokens: 16384,
    })

    const options = {
      hostname: '127.0.0.1',
      port: 8325,
      path: '/v1/chat/completions',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(data),
      },
    }

    const req = http.request(options, (res) => {
      let body = ''
      res.on('data', (chunk) => { body += chunk })
      res.on('end', () => {
        try {
          const parsed = JSON.parse(body)
          if (parsed.choices && parsed.choices[0]) {
            resolve(parsed.choices[0].message.content)
          } else if (parsed.error) {
            reject(new Error(`API error: ${parsed.error.message}`))
          } else {
            reject(new Error(`Unexpected response: ${body.substring(0, 200)}`))
          }
        } catch (e) {
          reject(new Error(`Parse error: ${e.message}\nBody: ${body.substring(0, 200)}`))
        }
      })
    })

    req.on('error', reject)
    req.write(data)
    req.end()
  })
}

function buildMessages(langCode, langName, batch) {
  const jsonStr = JSON.stringify(batch, null, 2)
  return [
    {
      role: 'system',
      content: `You are a professional translator. Translate the following JSON object from English to ${langName} (${langCode}).

RULES:
1. Keep ALL keys exactly as they are - only translate the string VALUES
2. Output ONLY valid JSON - no markdown, no explanation
3. Preserve HTML tags inside values (e.g., <strong>, <a href="...">)
4. Preserve variables/placeholders inside {{ }} — do NOT translate them
5. Preserve emoji characters (→, ✅, ❌, ⚠️, ▲, ●, etc.)
6. For ${langCode}: use proper ${langName} script (not romanization)
7. Keep text length reasonable - don't expand dramatically`
    },
    {
      role: 'user',
      content: `Translate this JSON to ${langName}:\n\n\`\`\`json\n${jsonStr}\n\`\`\``
    }
  ]
}

async function translateBatch(langCode, langName, entries) {
  const messages = buildMessages(langCode, langName, entries)
  
  for (let attempt = 0; attempt < 3; attempt++) {
    try {
      console.log(`  [${langCode}] Attempt ${attempt + 1}...`)
      const result = await callAPI(messages)
      
      // Extract JSON from response (might be wrapped in markdown)
      let jsonStr = result.trim()
      if (jsonStr.startsWith('```')) {
        jsonStr = jsonStr.replace(/^```(?:json)?\s*\n?/, '').replace(/\n?```$/, '')
      }
      
      const parsed = JSON.parse(jsonStr)
      console.log(`  [${langCode}] ✅ Success (${Object.keys(parsed).length} components)`)
      return parsed
    } catch (err) {
      console.error(`  [${langCode}] ❌ Attempt ${attempt + 1} failed: ${err.message}`)
      if (attempt < 2) {
        const wait = (attempt + 1) * 5000
        console.log(`  Waiting ${wait}ms...`)
        await sleep(wait)
      }
    }
  }
  
  console.error(`  [${langCode}] ❌ All attempts failed!`)
  return null
}

async function main() {
  // Split EN data into batches for translation
  const allEntries = []
  for (const [comp, keys] of Object.entries(enData)) {
    for (const [key, value] of Object.entries(keys)) {
      allEntries.push({ comp, key, value })
    }
  }
  
  const BATCH_SIZE = 150
  const batches = []
  for (let i = 0; i < allEntries.length; i += BATCH_SIZE) {
    const batch = {}
    for (const entry of allEntries.slice(i, i + BATCH_SIZE)) {
      if (!batch[entry.comp]) batch[entry.comp] = {}
      batch[entry.comp][entry.key] = entry.value
    }
    batches.push(batch)
  }
  
  console.log(`Total entries: ${allEntries.length}, batches: ${batches.length}`)
  
  for (const target of TARGETS) {
    console.log(`\n=== Translating to ${target.name} (${target.code}) ===`)
    
    const result = {}
    let batchNum = 0
    
    for (const batch of batches) {
      batchNum++
      console.log(`  Batch ${batchNum}/${batches.length}...`)
      
      const translated = await translateBatch(target.code, target.name, batch)
      if (translated) {
        Object.assign(result, translated)
      } else {
        // Fallback: use EN directly
        Object.assign(result, batch)
        console.log(`  ⚠️  Using EN fallback for batch ${batchNum}`)
      }
      
      // Rate limiting delay
      await sleep(2000)
    }
    
    // Write result
    const outputPath = path.join(LOCALE_DIR, `${target.code}.json`)
    fs.writeFileSync(outputPath, JSON.stringify(result, null, 2) + '\n', 'utf-8')
    console.log(`  ✅ ${target.code}.json written (${fs.statSync(outputPath).size} bytes)`)
  }
  
  console.log('\n🎉 All translations complete!')
}

main().catch(console.error)
