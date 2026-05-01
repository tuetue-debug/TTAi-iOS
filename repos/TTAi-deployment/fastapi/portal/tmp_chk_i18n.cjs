const fs = require('fs');
const b = 'C:/Users/vannt-pc/.openclaw/workspace/repos/TTAi-deployment/fastapi/portal/src/pages/';

const pages = ['LandingPage','LoginPage','SignupPage','ApiKeysPage','BillingPage',
  'DocsPage','FeaturesPage','LimitsPage','OverviewPage','ProfilePage','UsagePage',
  'AboutPage','PrivacyPolicyPage','TermsOfUsePage','OpenClawSetupPage',
  'OpenClawBundlesPage','OpenClawPresetsPage'];

pages.forEach(p => {
  const c = fs.readFileSync(b + p + '.vue', 'utf-8');
  const count = c.split("$t(").length - 1;
  console.log(p + ': ' + count + ' t() calls');
});
