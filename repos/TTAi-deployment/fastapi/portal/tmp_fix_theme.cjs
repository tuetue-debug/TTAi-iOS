const fs = require('fs');
const path = 'C:/Users/vannt-pc/.openclaw/workspace/repos/TTAi-deployment/fastapi/portal/src/components/TopNav.vue';
let c = fs.readFileSync(path, 'utf-8');

// Replace HTML entities with actual unicode char literals
c = c.replace('&#x2600;', '\u2600');
c = c.replace('&#x263E;', '\u263E');

fs.writeFileSync(path, c, 'utf-8');
console.log('Done. Verifying:');
const verify = fs.readFileSync(path, 'utf-8');
console.log('Contains ☀:', verify.includes('\u2600'));
console.log('Contains ☾:', verify.includes('\u263E'));
