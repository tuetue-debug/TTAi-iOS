/**
 * translate-component.cjs - Translate one JSON component at a time
 * using openclaw's sessions_spawn mechanism.
 * 
 * Usage: node translate-component.cjs <componentName> <lang>
 * 
 * Reads en.json, extracts one component, spawns subagent to translate,
 * writes output to <lang>_<componentName>.json
 */

const path = require('path');
const fs = require('fs');
const { execSync } = require('child_process');

const localeDir = 'C:/Users/vannt-pc/.openclaw/workspace/repos/TTAi-deployment/fastapi/portal/src/i18n/locales';
const workspaceDir = 'C:/Users/vannt-pc/.openclaw/workspace';

// Read all components from en.json
const en = JSON.parse(fs.readFileSync(path.join(localeDir, 'en.json'), 'utf-8'));

// Log available components
console.log('Available components:');
Object.keys(en).forEach(k => {
  const jsonLen = JSON.stringify(en[k]).length;
  console.log(`  ${k}: ${jsonLen} bytes, ${Object.keys(en[k]).length} keys`);
});

// Suggest command for translation
console.log('\nTo translate one component, use:');
console.log('node translate-component.cjs <ComponentName> <lang>');
console.log('Example: node translate-component.cjs LandingPage vi');
