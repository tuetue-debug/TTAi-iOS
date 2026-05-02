<script setup>
import overviewImg from '../assets/help/overview.png'
import apiKeysImg from '../assets/help/api-keys.png'
import usageImg from '../assets/help/usage.png'
import docsImg from '../assets/help/docs.png'
</script>

<template>
  <div class="help-page">
    <header class="help-header">
      <router-link to="/" class="back-link">{{ $t('HelpPage.back') }}</router-link>
      <h1>{{ $t('HelpPage.title') }}</h1>
      <p class="help-subtitle">
        {{ $t('HelpPage.subtitle') }}
      </p>
    </header>

    <main class="help-grid">
      <router-link to="/start" class="help-menu-card">
        <div class="help-menu-icon">🚀</div>
        <h2>{{ $t('HelpPage.quickStartTitle') }}</h2>
        <p>{{ $t('HelpPage.quickStartDescription') }}</p>
        <figure class="help-figure">
          <img :src="overviewImg" :alt="$t('HelpPage.quickStartAlt')" class="help-figure-image" />
          <figcaption>{{ $t('HelpPage.quickStartCaption') }}</figcaption>
        </figure>
      </router-link>

      <router-link to="/guide" class="help-menu-card">
        <div class="help-menu-icon">📖</div>
        <h2>{{ $t('HelpPage.guideTitle') }}</h2>
        <p>{{ $t('HelpPage.guideDescription') }}</p>
        <figure class="help-figure">
          <img :src="apiKeysImg" :alt="$t('HelpPage.guideAlt')" class="help-figure-image" />
          <figcaption>{{ $t('HelpPage.guideCaption') }}</figcaption>
        </figure>
      </router-link>

      <router-link to="/faq" class="help-menu-card">
        <div class="help-menu-icon">❓</div>
        <h2>{{ $t('HelpPage.faqTitle') }}</h2>
        <p>{{ $t('HelpPage.faqDescription') }}</p>
        <figure class="help-figure">
          <img :src="usageImg" :alt="$t('HelpPage.faqAlt')" class="help-figure-image" />
          <figcaption>{{ $t('HelpPage.faqCaption') }}</figcaption>
        </figure>
      </router-link>

      <router-link to="/contact" class="help-menu-card">
        <div class="help-menu-icon">💬</div>
        <h2>{{ $t('HelpPage.contactTitle') }}</h2>
        <p>{{ $t('HelpPage.contactDescription') }}</p>
        <figure class="help-figure">
          <img :src="docsImg" :alt="$t('HelpPage.contactAlt')" class="help-figure-image" />
          <figcaption>{{ $t('HelpPage.contactCaption') }}</figcaption>
        </figure>
      </router-link>
    </main>

    <footer class="site-footer document-footer">
      <span class="footer-links">
        <router-link to="/terms-of-use">{{ $t('TermsOfUsePage.termsOfService') }}</router-link>
        &middot;
        <router-link to="/privacy-policy">{{ $t('TermsOfUsePage.privacyPolicy') }}</router-link>
        &middot;
        <router-link to="/about">{{ $t('LandingPage.about') }}</router-link>
      </span>
      <span>Copyright 2026 &copy; <a href="https://minhtue.vn" target="_blank" rel="noopener">{{ $t('TermsOfUsePage.minhTueTradingInvestmentJsc') }}</a></span>
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
  max-width: 1180px;
  margin: 0 auto 28px;
}
.back-link {
  display: inline-block;
  margin-bottom: 12px;
  color: var(--text-muted);
  font-size: 13px;
}
.back-link:hover { color: var(--accent); }
.help-header h1 {
  margin: 0 0 10px;
  font-size: 38px;
  line-height: 1.1;
  letter-spacing: -0.03em;
}
.help-subtitle {
  margin: 0;
  max-width: 880px;
  color: var(--text-muted);
  font-size: 15px;
  line-height: 1.7;
}
.help-grid {
  max-width: 1180px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 24px;
}
.help-menu-card {
  display: flex;
  flex-direction: column;
  border: 1px solid var(--border);
  background: var(--bg-card);
  border-radius: 24px;
  padding: 28px;
  box-shadow: var(--shadow);
  text-decoration: none;
  color: inherit;
  transition: transform 0.15s, box-shadow 0.15s;
}
.help-menu-card:hover {
  transform: translateY(-3px);
  box-shadow: var(--shadow-elevated);
}
.help-menu-icon {
  font-size: 36px;
  margin-bottom: 4px;
}
.help-menu-card h2 {
  margin: 0 0 8px;
  font-size: 24px;
  letter-spacing: -0.02em;
}
.help-menu-card p {
  margin: 0 0 16px;
  color: var(--text-secondary);
  line-height: 1.6;
  flex: 1;
}
.help-figure {
  margin: 0;
  border: 1px dashed var(--border-active);
  border-radius: 16px;
  background: color-mix(in srgb, var(--accent-soft) 45%, transparent);
  padding: 12px;
}
.help-figure-image {
  width: 100%;
  display: block;
  border-radius: 10px;
  border: 1px solid var(--border);
}
.help-figure figcaption {
  margin-top: 8px;
  text-align: center;
  color: var(--text-muted);
  font-size: 13px;
}
.document-footer {
  position: relative;
  bottom: auto;
  left: auto;
  text-align: center;
  margin-top: 28px;
  padding-bottom: 12px;
  display: flex;
  gap: 14px;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  max-width: 1180px;
  margin-left: auto;
  margin-right: auto;
}

@media (max-width: 820px) {
  .help-grid { grid-template-columns: 1fr; }
}
@media (max-width: 640px) {
  .help-page { padding: 14px; }
  .help-header h1 { font-size: 30px; }
  .help-menu-card { padding: 20px; }
}
</style>
