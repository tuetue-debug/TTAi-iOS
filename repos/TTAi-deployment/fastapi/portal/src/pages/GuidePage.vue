<script setup>
import overviewImg from '../assets/help/overview.png'
import apiKeysImg from '../assets/help/api-keys.png'
import usageImg from '../assets/help/usage.png'
import billingImg from '../assets/help/billing.png'
import docsImg from '../assets/help/docs.png'
import profileImg from '../assets/help/profile.png'
</script>

<template>
  <div class="help-page">
    <header class="help-header">
      <router-link to="/help" class="back-link">{{ $t('GuidePage.back') }}</router-link>
      <div class="eyebrow">{{ $t('GuidePage.eyebrow') }}</div>
      <h1>{{ $t('GuidePage.title') }}</h1>
      <p class="help-subtitle">{{ $t('GuidePage.subtitle') }}</p>
    </header>

    <main class="help-content">
      <article class="help-card">
        <h3>{{ $t('GuidePage.overviewTitle') }}</h3>
        <p v-html="$t('GuidePage.overviewPurpose')"></p>
        <p v-html="$t('GuidePage.overviewWhenToUse')"></p>
        <ul>
          <li>{{ $t('GuidePage.overviewItem1') }}</li>
          <li v-html="$t('GuidePage.overviewItem2')"></li>
          <li v-html="$t('GuidePage.overviewItem3')"></li>
        </ul>
        <p class="help-note" v-html="$t('GuidePage.overviewNote')"></p>
        <figure class="help-figure small">
          <img :src="overviewImg" :alt="$t('GuidePage.overviewAlt')" class="help-figure-image" />
          <figcaption v-html="$t('GuidePage.overviewFigCaption')"></figcaption>
        </figure>
      </article>

      <article class="help-card">
        <h3>{{ $t('GuidePage.apiKeysTitle') }}</h3>
        <p v-html="$t('GuidePage.apiKeysPurpose')"></p>
        <p v-html="$t('GuidePage.apiKeysSteps')"></p>
        <ol class="action-list compact">
          <li v-html="$t('GuidePage.apiKeysStep1')"></li>
          <li v-html="$t('GuidePage.apiKeysStep2')"></li>
          <li v-html="$t('GuidePage.apiKeysStep3')"></li>
          <li>{{ $t('GuidePage.apiKeysStep4') }}</li>
        </ol>
        <p v-html="$t('GuidePage.apiKeysWhenToRevoke')"></p>
        <p class="help-note" v-html="$t('GuidePage.apiKeysNote')"></p>
        <figure class="help-figure small">
          <img :src="apiKeysImg" :alt="$t('GuidePage.apiKeysAlt')" class="help-figure-image" />
          <figcaption v-html="$t('GuidePage.apiKeysFigCaption')"></figcaption>
        </figure>
      </article>

      <article class="help-card">
        <h3>{{ $t('GuidePage.usageTitle') }}</h3>
        <p v-html="$t('GuidePage.usagePurpose')"></p>
        <ul>
          <li v-html="$t('GuidePage.usageTotalRequests')"></li>
          <li v-html="$t('GuidePage.usageSuccessfulRequests')"></li>
          <li v-html="$t('GuidePage.usageErrorRequests')"></li>
          <li v-html="$t('GuidePage.usageTotalTokens')"></li>
        </ul>
        <p v-html="$t('GuidePage.usageIfErrors')"></p>
        <figure class="help-figure small">
          <img :src="usageImg" :alt="$t('GuidePage.usageAlt')" class="help-figure-image" />
          <figcaption v-html="$t('GuidePage.usageFigCaption')"></figcaption>
        </figure>
      </article>

      <article class="help-card">
        <h3>{{ $t('GuidePage.billingTitle') }}</h3>
        <p v-html="$t('GuidePage.billingPurpose')"></p>
        <ol class="action-list compact">
          <li>{{ $t('GuidePage.billingStep1') }}</li>
          <li v-html="$t('GuidePage.billingStep2')"></li>
          <li>{{ $t('GuidePage.billingStep3') }}</li>
          <li>{{ $t('GuidePage.billingStep4') }}</li>
        </ol>
        <p v-html="$t('GuidePage.billingGTGT')"></p>
        <p class="help-note" v-html="$t('GuidePage.billingNote')"></p>
        <figure class="help-figure small">
          <img :src="billingImg" :alt="$t('GuidePage.billingAlt')" class="help-figure-image" />
          <figcaption v-html="$t('GuidePage.billingFigCaption')"></figcaption>
        </figure>
      </article>

      <article class="help-card">
        <h3>{{ $t('GuidePage.limitsTitle') }}</h3>
        <p v-html="$t('GuidePage.limitsPurpose')"></p>
        <ul>
          <li v-html="$t('GuidePage.limitsBlockedEvents')"></li>
          <li v-html="$t('GuidePage.limitsTopReason')"></li>
          <li v-html="$t('GuidePage.limitsScope')"></li>
        </ul>
        <p v-html="$t('GuidePage.limitsWhenToCheck')"></p>
        <ol class="action-list compact">
          <li v-html="$t('GuidePage.limitsStep1')"></li>
          <li v-html="$t('GuidePage.limitsStep2')"></li>
          <li v-html="$t('GuidePage.limitsStep3')"></li>
        </ol>
        <p class="help-note" v-html="$t('GuidePage.limitsNote')"></p>
      </article>

      <article class="help-card">
        <h3>{{ $t('GuidePage.docsTitle') }}</h3>
        <p v-html="$t('GuidePage.docsPurpose')"></p>
        <ol class="action-list compact">
          <li v-html="$t('GuidePage.docsStep1')"></li>
          <li v-html="$t('GuidePage.docsStep2')"></li>
          <li v-html="$t('GuidePage.docsStep3')"></li>
          <li>{{ $t('GuidePage.docsStep4') }}</li>
        </ol>
        <p class="help-note" v-html="$t('GuidePage.docsNote')"></p>
        <figure class="help-figure small">
          <img :src="docsImg" :alt="$t('GuidePage.docsAlt')" class="help-figure-image" />
          <figcaption v-html="$t('GuidePage.docsFigCaption')"></figcaption>
        </figure>
      </article>

      <article class="help-card">
        <h3>{{ $t('GuidePage.integrationsTitle') }}</h3>
        <p v-html="$t('GuidePage.integrationsPurpose')"></p>
        <ul>
          <li v-html="$t('GuidePage.integrationsSetup')"></li>
          <li v-html="$t('GuidePage.integrationsBundles')"></li>
          <li v-html="$t('GuidePage.integrationsPresets')"></li>
          <li v-html="$t('GuidePage.integrationsTargets')"></li>
        </ul>
        <p v-html="$t('GuidePage.integrationsNewUser')"></p>
        <ol class="action-list compact">
          <li v-html="$t('GuidePage.integrationsStep1')"></li>
          <li v-html="$t('GuidePage.integrationsStep2')"></li>
          <li v-html="$t('GuidePage.integrationsStep3')"></li>
          <li v-html="$t('GuidePage.integrationsStep4')"></li>
          <li v-html="$t('GuidePage.integrationsStep5')"></li>
        </ol>
        <p class="help-note" v-html="$t('GuidePage.integrationsNote')"></p>
      </article>

      <article class="help-card">
        <h3>{{ $t('GuidePage.profileTitle') }}</h3>
        <p v-html="$t('GuidePage.profilePurpose')"></p>
        <ul>
          <li>{{ $t('GuidePage.profileItem1') }}</li>
          <li>{{ $t('GuidePage.profileItem2') }}</li>
        </ul>
        <p class="help-note" v-html="$t('GuidePage.profileNote')"></p>
        <figure class="help-figure small">
          <img :src="profileImg" :alt="$t('GuidePage.profileAlt')" class="help-figure-image" />
          <figcaption v-html="$t('GuidePage.profileFigCaption')"></figcaption>
        </figure>
      </article>
    </main>

    <footer class="site-footer document-footer">
      <router-link to="/help">{{ $t('GuidePage.backToHelp') }}</router-link>
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
.help-card {
  border: 1px solid var(--border);
  background: var(--bg-card);
  border-radius: 24px;
  padding: 28px;
  box-shadow: var(--shadow);
}
.help-card h3 {
  margin: 0 0 10px;
  font-size: 24px;
}
.help-card p, .help-card li {
  color: var(--text-secondary);
  line-height: 1.7;
}
.action-list {
  margin: 14px 0;
  padding-left: 22px;
}
.action-list.compact { margin: 10px 0; }
.help-note {
  border-left: 3px solid var(--accent);
  padding-left: 12px;
}
.help-figure {
  margin: 18px 0 0;
  border: 1px dashed var(--border-active);
  border-radius: 16px;
  background: color-mix(in srgb, var(--accent-soft) 45%, transparent);
  padding: 16px;
}
.help-figure.small { margin-top: 14px; }
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
  .help-card { padding: 20px; }
}
</style>
