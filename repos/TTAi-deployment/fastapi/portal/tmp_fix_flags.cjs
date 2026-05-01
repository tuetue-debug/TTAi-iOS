const fs = require("fs");
const path = "C:/Users/vannt-pc/.openclaw/workspace/repos/TTAi-deployment/fastapi/portal/src/components/TopNav.vue";
let content = fs.readFileSync(path, "utf-8");
content = content.replace(/flag: `[^`]+`/g, (m) => m);
// Replace the broken flag sequences  
const replacements = [
  ["dYاdY�,", "🇺🇸"],
  ["dYدdY�3", "🇻🇳"],
  ["dYخdY��", "🇫🇷"],
  ['dY�"dY�3', "🇨🇳"],
  ["dY��dY��", "🇰🇷"],
  ["dY�_dY��", "🇯🇵"],
];
for (const [from, to] of replacements) {
  content = content.replace(from, to);
}
fs.writeFileSync(path, content, "utf-8");
// Verify
const match = content.match(/value: `en`[^}]+}/);
if (match) console.log("EN locale:", match[0].trim());
const hasEmoji = /[\u{1F1E6}-\u{1F1FF}]/u.test(content);
console.log("Has real emoji flags:", hasEmoji);
