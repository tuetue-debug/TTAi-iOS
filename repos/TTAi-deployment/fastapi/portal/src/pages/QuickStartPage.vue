<script setup>
import overviewImg from '../assets/help/overview.png'
</script>

<template>
  <div class="help-page">
    <header class="help-header">
      <router-link to="/help" class="back-link">{{ $t('QuickStartPage.back') }}</router-link>
      <div class="eyebrow">{{ $t('QuickStartPage.eyebrow') }}</div>
      <h1>{{ $t('QuickStartPage.title') }}</h1>
      <p class="help-subtitle">
        {{ $t('QuickStartPage.subtitle') }}
      </p>
    </header>

    <main class="help-content">
      <ol class="action-list big">
        <li v-html="$t('QuickStartPage.step1')"></li>
        <li v-html="$t('QuickStartPage.step2')"></li>
        <li>{{ $t('QuickStartPage.step3') }}</li>
        <li v-html="$t('QuickStartPage.step4')"></li>
        <li v-html="$t('QuickStartPage.step5')"></li>
        <li v-html="$t('QuickStartPage.step6')"></li>
      </ol>
      <figure class="help-figure">
        <img :src="overviewImg" :alt="$t('QuickStartPage.figAlt')" class="help-figure-image" />
        <figcaption v-html="$t('QuickStartPage.figCaption')"></figcaption>
      </figure>
    </main>

    <footer class="site-footer document-footer">
      <router-link to="/help">{{ $t('QuickStartPage.backToHelp') }}</router-link>
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
.action-list.big {
  margin: 0 0 24px;
  padding-left: 28px;
}
.action-list.big li {
  margin-bottom: 12px;
  line-height: 1.7;
  font-size: 16px;
  color: var(--text-secondary);
}
.help-figure {
  border: 1px dashed var(--border-active);
  border-radius: 16px;
  background: color-mix(in srgb, var(--accent-soft) 45%, transparent);
  padding: 16px;
}
.help-figure-image {
  width: 100%;
  display: block;
  border-radius: 12px;
  border: 1px solid var(--border);
}
.help-figure figcaption {
  margin-top: 12px;
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
