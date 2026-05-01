<template>
  <div class="portal-shell">
    <TopNav />

    <main>
      <section class="hero-grid">
        <div class="hero-chat-panel">
          <LandingChat />
        </div>

        <AuthCard mode="login" :compact="true" />
      </section>

      <section id="console" class="console-preview">
        <div class="section-heading">
          <span class="eyebrow">{{ $t('LandingPage.consolePreview') }}</span>
          <h3>{{ $t('LandingPage.theFirstMvpPagesAlready') }}</h3>
          <p>
            This portal will let a developer sign up, create keys, inspect usage, understand
            billing, and start using the API without touching internal admin surfaces.
          </p>
        </div>

        <div class="preview-grid">
          <article class="preview-card strong">
            <div class="preview-label">{{ $t('LandingPage.dashboard') }}</div>
            <div class="preview-metric">$12.48</div>
            <p>{{ $t('LandingPage.estimatedSpendUsageTrendLatest') }}</p>
          </article>
          <article class="preview-card">
            <div class="preview-label">{{ $t('LandingPage.apiKeys') }}</div>
            <ul>
              <li>{{ $t('LandingPage.scopedKeys') }}</li>
              <li>{{ $t('LandingPage.lastUsedTracking') }}</li>
              <li>{{ $t('LandingPage.safeRevokeFlow') }}</li>
            </ul>
          </article>
          <article class="preview-card">
            <div class="preview-label">{{ $t('LandingPage.usageLimits') }}</div>
            <ul>
              <li>{{ $t('LandingPage.dailyUsageCharts') }}</li>
              <li>{{ $t('LandingPage.quotaOverview') }}</li>
              <li>{{ $t('LandingPage.tenantprojectReadyModel') }}</li>
            </ul>
          </article>
          <article class="preview-card">
            <div class="preview-label">{{ $t('LandingPage.billingDocs') }}</div>
            <ul>
              <li>{{ $t('LandingPage.billableEventSummary') }}</li>
              <li>{{ $t('LandingPage.limitsUnderstanding') }}</li>
              <li>{{ $t('LandingPage.referencePlaygroundNext') }}</li>
            </ul>
          </article>
        </div>
      </section>
    </main>

    <footer class="site-footer">
      <span class="footer-links">
        <router-link to="/terms-of-use">{{ $t('LandingPage.termsOfService') }}</router-link>
        &middot;
        <router-link to="/privacy-policy">{{ $t('LandingPage.privacyPolicy') }}</router-link>
        &middot;
        <router-link to="/about">{{ $t('LandingPage.about') }}</router-link>
      </span>
      <span>Copyright 2026 &copy; <a href="https://minhtue.vn" target="_blank" rel="noopener">{{ $t('LandingPage.minhTueTradingInvestmentJsc') }}</a></span>
    </footer>
  </div>
</template>

<script setup>
import TopNav from '../components/TopNav.vue'
import AuthCard from '../components/AuthCard.vue'
import LandingChat from '../components/LandingChat.vue'
</script>
