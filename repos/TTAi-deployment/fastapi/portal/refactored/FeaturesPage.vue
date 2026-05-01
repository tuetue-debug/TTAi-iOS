<template>
  <div class="legal-page">
    <header class="legal-header">
      <router-link to="/" class="back-link">← Back to Console</router-link>
      <h1>Features</h1>
      <p class="legal-effective">Everything you need to build with AI — powered by Tue Tue</p>
    </header>

    <section class="legal-body features-body">
      <!-- Row 1: Core API -->
      <div class="feature-section">
        <h2>Core API</h2>
        <div class="feature-grid">
          <div class="feature-card">
            <div class="feature-icon">🔌</div>
            <h3>OpenAI-Compatible API</h3>
            <p>Drop-in replacement for OpenAI's chat completions and embeddings endpoints. Use your existing SDKs and libraries — no code changes needed.</p>
          </div>
          <div class="feature-card">
            <div class="feature-icon">🧠</div>
            <h3>Multiple Model Access</h3>
            <p>Choose from a curated selection of leading open-source and proprietary models — from lightweight 4B models for simple tasks to advanced 70B+ models for complex reasoning.</p>
          </div>
          <div class="feature-card">
            <div class="feature-icon">📝</div>
            <h3>Streaming & Non-Streaming</h3>
            <p>Support for both real-time streaming responses (SSE) and standard non-streaming requests. Streaming delivers partial results as they're generated.</p>
          </div>
          <div class="feature-card">
            <div class="feature-icon">📐</div>
            <h3>Embeddings</h3>
            <p>Generate vector embeddings for text — ideal for semantic search, clustering, classification, and RAG (Retrieval-Augmented Generation) pipelines.</p>
          </div>
          <div class="feature-card">
            <div class="feature-icon">🔍</div>
            <h3>Function Calling</h3>
            <p>Connect models to external tools and APIs. Define functions in familiar JSON schema format, and let the model decide when to call them.</p>
          </div>
          <div class="feature-card">
            <div class="feature-icon">🖼️</div>
            <h3>Vision (Image Input)</h3>
            <p>Send images to supported models for analysis, description, and understanding. Works with standard base64-encoded or URL-based image inputs.</p>
          </div>
        </div>
      </div>

      <!-- Row 2: Platform -->
      <div class="feature-section">
        <h2>Platform</h2>
        <div class="feature-grid">
          <div class="feature-card">
            <div class="feature-icon">🔐</div>
            <h3>API Key Management</h3>
            <p>Create, scope, and revoke API keys from the console. Track last-used timestamps and monitor usage per key.</p>
          </div>
          <div class="feature-card">
            <div class="feature-icon">📊</div>
            <h3>Usage Analytics</h3>
            <p>Real-time visibility into your token consumption, request volume, and cost — broken down by model, time period, and API key.</p>
          </div>
          <div class="feature-card">
            <div class="feature-icon">💰</div>
            <h3>Transparent Pricing</h3>
            <p>Pay only for what you use. No hidden fees, no upfront commitments. Pricing is published per-model per-million-tokens.</p>
          </div>
          <div class="feature-card">
            <div class="feature-icon">🎯</div>
            <h3>Rate Limiting & Quotas</h3>
            <p>Understand your plan limits at a glance. Configure alerts when approaching quota thresholds. Upgrade or scale as you grow.</p>
          </div>
          <div class="feature-card">
            <div class="feature-icon">🚀</div>
            <h3>Fast Inference</h3>
            <p>Optimized inference pipeline with intelligent request routing and caching for sub-second response times on common workloads.</p>
          </div>
          <div class="feature-card">
            <div class="feature-icon">🌐</div>
            <h3>Vietnamese-First</h3>
            <p>Models optimized for Vietnamese language understanding and generation. Better accuracy, tone, and cultural context than generic English-first models.</p>
          </div>
        </div>
      </div>

      <!-- Row 3: Developer Experience -->
      <div class="feature-section">
        <h2>Developer Experience</h2>
        <div class="feature-grid">
          <div class="feature-card">
            <div class="feature-icon">📖</div>
            <h3>Comprehensive Docs</h3>
            <p>Detailed API reference, quickstart guides, and code examples in multiple languages (curl, Python, JavaScript, Go).</p>
          </div>
          <div class="feature-card">
            <div class="feature-icon">🛠️</div>
            <h3>OpenClaw Integration</h3>
            <p>One-click setup to connect OpenClaw agents with Tue Tue API. Generate pre-configured bundles, presets, and provider configs.</p>
          </div>
          <div class="feature-card">
            <div class="feature-icon">📥</div>
            <h3>SDK Support</h3>
            <p>Use any OpenAI-compatible SDK (Python, Node.js, Go, Java, etc.) to interact with Tue Tue API. No custom libraries needed.</p>
          </div>
          <div class="feature-card">
            <div class="feature-icon">🧪</div>
            <h3>Playground (Coming Soon)</h3>
            <p>Test models interactively in your browser before writing code. Experiment with parameters, system prompts, and model selection.</p>
          </div>
          <div class="feature-card">
            <div class="feature-icon">📄</div>
            <h3>Invoice & Billing API</h3>
            <p>Programmatically access your billing data, download VAT invoices, and manage subscriptions through dedicated API endpoints.</p>
          </div>
          <div class="feature-card">
            <div class="feature-icon">🔔</div>
            <h3>Webhook Alerts (Coming Soon)</h3>
            <p>Receive real-time notifications for usage thresholds, billing events, and service status changes via webhooks.</p>
          </div>
        </div>
      </div>

      <!-- Row 4: Enterprise -->
      <div class="feature-section">
        <h2>Enterprise</h2>
        <div class="feature-grid">
          <div class="feature-card enterprise">
            <div class="feature-icon">🛡️</div>
            <h3>Data Privacy</h3>
            <p>Your data stays yours. Opt out of training at any time. Enterprise customers are never used for model training by default. Full compliance with Vietnamese data protection laws.</p>
          </div>
          <div class="feature-card enterprise">
            <div class="feature-icon">🔒</div>
            <h3>Encryption</h3>
            <p>End-to-end encryption in transit (TLS 1.3) and at rest. Industry-standard security practices, regular audits, and incident response procedures.</p>
          </div>
          <div class="feature-card enterprise">
            <div class="feature-icon">🤝</div>
            <h3>Dedicated Support</h3>
            <p>Priority support with SLAs for enterprise plans. Direct access to our engineering team for integration assistance and troubleshooting.</p>
          </div>
          <div class="feature-card enterprise">
            <div class="feature-icon">⚡</div>
            <h3>Custom Deployment</h3>
            <p>Need dedicated infrastructure? We offer private deployments with isolated compute, custom model fine-tuning, and on-premise options for qualifying customers.</p>
          </div>
        </div>
      </div>
    </section>

    <footer class="site-footer document-footer">
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

<style scoped>
.legal-page {
  min-height: 100vh;
  padding: 24px;
  background: var(--gradient-bg);
  color: var(--text-primary);
}
.legal-header {
  max-width: 1040px;
  margin: 0 auto 32px;
}
.back-link {
  display: inline-block;
  margin-bottom: 12px;
  color: var(--text-muted);
  font-size: 13px;
}
.back-link:hover { color: var(--accent); }
.legal-header h1 {
  margin: 8px 0 6px;
  font-size: 36px;
  letter-spacing: -0.03em;
  line-height: 1.1;
}
.legal-effective {
  color: var(--text-muted);
  font-size: 14px;
  margin: 0;
}
.features-body {
  max-width: 1040px;
  margin: 0 auto;
  padding: 40px;
  border-radius: 28px;
  border: 1px solid var(--border);
  background: var(--bg-card);
  box-shadow: var(--shadow);
}

.feature-section {
  margin-bottom: 48px;
}
.feature-section h2 {
  margin: 0 0 20px;
  font-size: 24px;
  letter-spacing: -0.02em;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: 10px;
}
.feature-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}
.feature-card {
  padding: 24px;
  border-radius: 20px;
  border: 1px solid var(--border);
  background: var(--bg-subtle);
  transition: all 0.18s ease;
}
.feature-card:hover {
  box-shadow: var(--shadow-hover);
  transform: translateY(-2px);
}
.feature-card.enterprise {
  background: linear-gradient(135deg, var(--bg-subtle) 0%, var(--accent-soft) 100%);
  border-color: var(--border-active);
}
.feature-icon {
  font-size: 28px;
  margin-bottom: 12px;
}
.feature-card h3 {
  margin: 0 0 8px;
  font-size: 17px;
  letter-spacing: -0.01em;
  color: var(--text-primary);
}
.feature-card p {
  margin: 0;
  color: var(--text-secondary);
  font-size: 14px;
  line-height: 1.6;
}
.document-footer {
  position: relative;
  bottom: auto;
  left: auto;
  text-align: center;
  margin-top: 32px;
  padding-bottom: 12px;
  display: flex;
  gap: 14px;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
}

@media (max-width: 900px) {
  .feature-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
@media (max-width: 640px) {
  .legal-page { padding: 14px; }
  .features-body { padding: 24px; }
  .legal-header h1 { font-size: 28px; }
  .feature-grid {
    grid-template-columns: 1fr;
  }
}
</style>
