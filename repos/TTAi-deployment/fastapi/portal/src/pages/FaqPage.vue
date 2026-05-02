<template>
  <div class="help-page">
    <header class="help-header">
      <router-link to="/help" class="back-link">{{ $t('FaqPage.back') }}</router-link>
      <div class="eyebrow">{{ $t('FaqPage.eyebrow') }}</div>
      <h1>{{ $t('FaqPage.title') }}</h1>
      <p class="help-subtitle">{{ $t('FaqPage.subtitle') }}</p>
    </header>

    <main class="help-content">
      <div class="faq-list">
        <article class="faq-item">
          <h3>{{ $t('FaqPage.q1') }}</h3>
          <p>{{ $t('FaqPage.a1') }}</p>
        </article>
        <article class="faq-item">
          <h3>{{ $t('FaqPage.q2') }}</h3>
          <p>{{ $t('FaqPage.a2') }}</p>
        </article>
        <article class="faq-item">
          <h3>{{ $t('FaqPage.q3') }}</h3>
          <p>{{ $t('FaqPage.a3') }}</p>
        </article>
        <article class="faq-item">
          <h3>{{ $t('FaqPage.q4') }}</h3>
          <p>{{ $t('FaqPage.a4') }}</p>
        </article>
        <article class="faq-item">
          <h3>{{ $t('FaqPage.q5') }}</h3>
          <p>{{ $t('FaqPage.a5') }}</p>
        </article>
        <article class="faq-item">
          <h3>{{ $t('FaqPage.q6') }}</h3>
          <p>{{ $t('FaqPage.a6') }}</p>
        </article>
        <article class="faq-item">
          <h3>{{ $t('FaqPage.q7') }}</h3>
          <p>{{ $t('FaqPage.a7') }}</p>
        </article>
        <article class="faq-item">
          <h3>{{ $t('FaqPage.q8') }}</h3>
          <p>{{ $t('FaqPage.a8') }}</p>
        </article>
        <article class="faq-item">
          <h3>{{ $t('FaqPage.q9') }}</h3>
          <p v-html="$t('FaqPage.a9')"></p>
        </article>
        <article class="faq-item">
          <h3>{{ $t('FaqPage.q10') }}</h3>
          <p v-html="$t('FaqPage.a10')"></p>
        </article>
        <article class="faq-item">
          <h3>{{ $t('FaqPage.q11') }}</h3>
          <p>{{ $t('FaqPage.a11') }}</p>
        </article>
        <article class="faq-item">
          <h3>{{ $t('FaqPage.q12') }}</h3>
          <p>{{ $t('FaqPage.a12') }}</p>
        </article>
      </div>
    </main>

    <footer class="site-footer document-footer">
      <router-link to="/help">{{ $t('FaqPage.backToHelp') }}</router-link>
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
}
.faq-list {
  display: grid;
  gap: 12px;
}
.faq-item {
  border: 1px solid var(--border);
  background: var(--bg-card);
  border-radius: 20px;
  padding: 22px;
  box-shadow: var(--shadow);
}
.faq-item h3 {
  margin: 0 0 8px;
  font-size: 18px;
}
.faq-item p {
  margin: 0;
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

@media (max-width: 640px) {
  .help-page { padding: 14px; }
  .help-header h1 { font-size: 30px; }
}
</style>
