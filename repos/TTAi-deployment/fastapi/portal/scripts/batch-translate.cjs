/**
 * batch-translate.cjs - Translate en.json → vi.json via TTAi proxy
 * 
 * Splits into batches of ~10KB, calls proxy v2, writes properly.
 * Uses http agent with keepalive to avoid SSL issues.
 */

const fs = require('fs');
const http = require('http');

const localeDir = 'C:/Users/vannt-pc/.openclaw/workspace/repos/TTAi-deployment/fastapi/portal/src/i18n/locales';
const enPath = localeDir + '/en.json';
const targetLang = process.argv[2] || 'vi';
const targetLangName = process.argv[3] || 'Vietnamese';
const outPath = localeDir + '/' + targetLang + '.json';

const en = JSON.parse(fs.readFileSync(enPath, 'utf-8'));

// Split into batches of ~8KB (safe for model context)
const entries = Object.entries(en);
const batches = [];
let current = {};
let size = 0;

for (const [k, v] of entries) {
  const s = JSON.stringify(v).length;
  if (size + s > 8000 && Object.keys(current).length > 0) {
    batches.push({ ...current });
    current = {};
    size = 0;
  }
  current[k] = v;
  size += s;
}
if (Object.keys(current).length > 0) batches.push(current);

console.log(`EN: ${entries.length} components, ${batches.length} batches`);
batches.forEach((b, i) => {
  const s = JSON.stringify(b).length;
  console.log(`  Batch ${i}: ${Object.keys(b).length} components, ${s} bytes`);
});

const existing = {};
let completedBatches = 0;

// Load existing partial result
if (fs.existsSync(outPath)) {
  try {
    const existingData = JSON.parse(fs.readFileSync(outPath, 'utf-8'));
    Object.assign(existing, existingData);
    console.log(`Loaded existing: ${Object.keys(existing).length} components`);
  } catch(e) { console.log('No valid existing file, starting fresh'); }
}

function callApi(batch, batchIdx) {
  return new Promise((resolve, reject) => {
    const prompt = `Translate only the STRING VALUES in this JSON from English to ${targetLangName}. Keep all JSON keys EXACTLY the same. Preserve ${{}} moustache syntax, HTML entities, URLs, emails, code snippets as-is. Return ONLY valid JSON, no explanation. DO NOT leave any English untranslated except URLs/emails/code.

Input JSON:
${JSON.stringify(batch, null, 2)}`;

    const body = JSON.stringify({
      model: 'ttai-chat',
      messages: [{ role: 'user', content: prompt }],
      max_tokens: 8192,
      temperature: 0.1
    });

    const options = {
      hostname: '127.0.0.1',
      port: 8325,
      path: '/v1/chat/completions',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(body)
      },
      timeout: 120000
    };

    const req = http.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          const parsed = JSON.parse(data);
          const content = parsed.choices?.[0]?.message?.content || '';
          // Extract JSON from response (handle markdown fences)
          let jsonStr = content;
          const fenceMatch = content.match(/```(?:json)?\s*([\s\S]*?)```/);
          if (fenceMatch) jsonStr = fenceMatch[1];
          
          const translated = JSON.parse(jsonStr.trim());
          Object.assign(existing, translated);
          completedBatches++;
          console.log(`✅ Batch ${batchIdx} done (${completedBatches}/${batches.length})`);
          resolve();
        } catch(e) {
          console.error(`❌ Batch ${batchIdx} parse error:`, e.message);
          console.error('Response snippet:', data.substring(0, 200));
          resolve(); // continue despite error
        }
      });
    });
    
    req.on('error', reject);
    req.on('timeout', () => { req.destroy(); reject(new Error('timeout')); });
    req.write(body);
  });
}

(async () => {
  for (let i = 0; i < batches.length; i++) {
    console.log(`\nTranslating batch ${i} (${Object.keys(batches[i]).length} components)...`);
    try {
      await callApi(batches[i], i);
    } catch(e) {
      console.error(`Batch ${i} failed:`, e.message);
    }
    // Write progress after each batch
    fs.writeFileSync(outPath, JSON.stringify(existing, null, 2), 'utf-8');
    console.log(`Written: ${Object.keys(existing).length}/${entries.length} components`);
  }
  
  // Final validation
  console.log(`\n=== Done ===`);
  const final = JSON.parse(fs.readFileSync(outPath, 'utf-8'));
  const enComp = Object.keys(en);
  const viComp = Object.keys(final);
  
  console.log(`EN: ${enComp.length}, VI: ${viComp.length}`);
  const missing = enComp.filter(k => !viComp.includes(k));
  if (missing.length > 0) console.log(`Missing: ${missing.join(', ')}`);
  
  // Verify no mojibake
  const raw = fs.readFileSync(outPath, 'utf-8');
  const bad = raw.match(/[^\x20-\x7E\x0A\x0D\u00C0-\u024F\u1EA0-\u1EF9\u3000-\u303F\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF\uAC00-\uD7AF\uFE00-\uFE0F\u200B-\u200D\uFEFF\u2026\u201C-\u201D\u00A9\u00AE\u2122\u2600-\u27BF\s]/g);
  console.log(`Suspicious chars: ${bad ? bad.length : 0}`);
})();
