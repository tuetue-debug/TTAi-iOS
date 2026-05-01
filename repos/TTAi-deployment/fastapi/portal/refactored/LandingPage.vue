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
          <span class="eyebrow">CONSOLE PREVIEW</span>
          <h3>The first MVP pages already mapped.</h3>
          <p>
            This portal will let a developer sign up, create keys, inspect usage, understand
            billing, and start using the API without touching internal admin surfaces.
          </p>
        </div>

        <div class="preview-grid">
          <article class="preview-card strong">
            <div class="preview-label">Dashboard</div>
            <div class="preview-metric">$12.48</div>
            <p>Estimated spend, usage trend, latest key activity, and quick-start docs.</p>
          </article>
          <article class="preview-card">
            <div class="preview-label">API Keys</div>
            <ul>
              <li>Scoped keys</li>
              <li>Last used tracking</li>
              <li>Safe revoke flow</li>
            </ul>
          </article>
          <article class="preview-card">
            <div class="preview-label">Usage & Limits</div>
            <ul>
              <li>Daily usage charts</li>
              <li>Quota overview</li>
              <li>Tenant/project ready model</li>
            </ul>
          </article>
          <article class="preview-card">
            <div class="preview-label">Billing & Docs</div>
            <ul>
              <li>Billable event summary</li>
              <li>Limits understanding</li>
              <li>Reference + playground next</li>
            </ul>
          </article>
        </div>
      </section>
    </main>

    <footer class="site-footer">
      <span class="footer-links">
        <router-link to="/terms-of-use">Terms of Service</router-link>
        &middot;
        <router-link to="/privacy-policy">Privacy Policy</router-link>
        &middot;
        <router-link to="/about">About</router-link>
      </span>
      <span>Copyright 2026 &copy; <a href="https://minhtue.vn" target="_blank" rel="noopener">Minh Tue Trading Investment JSC</a></span>
    </footer>
  </div>
</template>

<script setup>
import TopNav from '../components/TopNav.vue'
import AuthCard from '../components/AuthCard.vue'
import LandingChat from '../components/LandingChat.vue'
</script>
