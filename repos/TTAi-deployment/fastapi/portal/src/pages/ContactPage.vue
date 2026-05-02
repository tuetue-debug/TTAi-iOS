<template>
  <div class="help-page">
    <header class="help-header">
      <router-link to="/help" class="back-link">{{ $t('ContactPage.back') }}</router-link>
      <div class="eyebrow">{{ $t('ContactPage.eyebrow') }}</div>
      <h1>{{ $t('ContactPage.title') }}</h1>
      <p class="help-subtitle">{{ $t('ContactPage.subtitle') }}</p>
    </header>

    <main class="help-content">
      <div class="contact-grid">
        <article class="contact-card">
          <h3>{{ $t('ContactPage.infoTitle') }}</h3>
          <ul>
            <li>{{ $t('ContactPage.infoItem1') }}</li>
            <li>{{ $t('ContactPage.infoItem2') }}</li>
            <li>{{ $t('ContactPage.infoItem3') }}</li>
            <li>{{ $t('ContactPage.infoItem4') }}</li>
            <li>{{ $t('ContactPage.infoItem5') }}</li>
          </ul>
        </article>
        <article class="contact-card">
          <h3>{{ $t('ContactPage.systemTitle') }}</h3>
          <ul>
            <li><span v-html="$t('ContactPage.systemConsole')"></span> <a href="https://console.tuetue.vn" target="_blank" rel="noopener">console.tuetue.vn</a></li>
            <li><span v-html="$t('ContactPage.systemApi')"></span> <a href="https://api.tuetue.vn" target="_blank" rel="noopener">api.tuetue.vn</a></li>
            <li><span v-html="$t('ContactPage.systemDocs')"></span> <a href="https://console.tuetue.vn/#/docs" target="_blank" rel="noopener">console.tuetue.vn/#/docs</a></li>
            <li><span v-html="$t('ContactPage.systemGuide')"></span> <a href="https://console.tuetue.vn/#/help" target="_blank" rel="noopener">console.tuetue.vn/#/help</a></li>
          </ul>
          <p class="help-note">{{ $t('ContactPage.systemNote') }}</p>
        </article>
      </div>

      <article class="tips-card">
        <h3>{{ $t('ContactPage.tipsTitle') }}</h3>
        <ul>
          <li v-html="$t('ContactPage.tipsItem1')"></li>
          <li v-html="$t('ContactPage.tipsItem2')"></li>
          <li v-html="$t('ContactPage.tipsItem3')"></li>
          <li v-html="$t('ContactPage.tipsItem4')"></li>
        </ul>
      </article>
    </main>

    <footer class="site-footer document-footer">
      <router-link to="/help">{{ $t('ContactPage.backToHelp') }}</router-link>
    </footer>
  </div>
</template>

<style scoped>
.help-page {
  min-height: 100vh;
  padding: 24px;
  background: var(--gradient-bg);
  color: var(--text-primary);
}
.help-header {
  max-width: 900px;
  margin: 0 auto 28px;
}
.back-link {
  display: inline-block;
  margin-bottom: 12px;
  color: var(--text-muted);
  font-size: 13px;
}
.back-link:hover { color: var(--accent); }
.eyebrow {
  font-size: 12px;
  font-weight: 800;
  color: var(--accent);
  letter-spacing: 0.1em;
  margin-bottom: 6px;
}
.help-header h1 {
  margin: 0 0 10px;
  font-size: 38px;
  line-height: 1.1;
  letter-spacing: -0.03em;
}
.help-subtitle {
  margin: 0;
  max-width: 700px;
  color: var(--text-muted);
  font-size: 15px;
  line-height: 1.7;
}
.help-content {
  max-width: 900px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.contact-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}
.contact-card, .tips-card {
  border: 1px solid var(--border);
  background: var(--bg-card);
  border-radius: 24px;
  padding: 28px;
  box-shadow: var(--shadow);
}
.contact-card h3, .tips-card h3 {
  margin: 0 0 14px;
  font-size: 22px;
}
.contact-card li, .tips-card li {
  color: var(--text-secondary);
  line-height: 1.8;
  margin-bottom: 6px;
}
.contact-card a {
  color: var(--accent);
}
.contact-card a:hover { opacity: 0.8; }
.help-note {
  border-left: 3px solid var(--accent);
  padding-left: 12px;
  margin-top: 16px;
  color: var(--text-secondary);
  line-height: 1.7;
}
.document-footer {
  max-width: 900px;
  margin: 28px auto 0;
  padding: 12px 0;
  text-align: center;
}
.document-footer a { color: var(--text-muted); font-size: 14px; }
.document-footer a:hover { color: var(--accent); }

@media (max-width: 720px) {
  .contact-grid { grid-template-columns: 1fr; }
}
@media (max-width: 640px) {
  .help-page { padding: 14px; }
  .help-header h1 { font-size: 30px; }
  .contact-card, .tips-card { padding: 20px; }
}
</style>
