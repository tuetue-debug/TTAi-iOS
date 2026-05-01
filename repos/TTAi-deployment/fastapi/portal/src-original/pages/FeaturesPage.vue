<template>
  <div class="legal-page">
    <header class="legal-header">
      <router-link to="/" class="back-link">â† Back to Console</router-link>
      <h1>{{ $t('FeaturesPage.features') }}</h1>
      <p class="legal-effective">Everything you need to build with AI â€” powered by Tue Tue</p>
    </header>

    <section class="legal-body features-body">
      <!-- Row 1: Core API -->
      <div class="feature-section">
        <h2>{{ $t('FeaturesPage.coreApi') }}</h2>
        <div class="feature-grid">
          <div class="feature-card">
            <div class="feature-icon">ðŸ”Œ</div>
            <h3>{{ $t('FeaturesPage.openaicompatibleApi') }}</h3>
            <p>Drop-in replacement for OpenAI's chat completions and embeddings endpoints. Use your existing SDKs and libraries â€” no code changes needed.</p>
          </div>
          <div class="feature-card">
            <div class="feature-icon">ðŸ§ </div>
            <h3>{{ $t('FeaturesPage.multipleModelAccess') }}</h3>
            <p>Choose from a curated selection of leading open-source and proprietary models â€” from lightweight 4B models for simple tasks to advanced 70B+ models for complex reasoning.</p>
          </div>
          <div class="feature-card">
            <div class="feature-icon">ðŸ“</div>
            <h3>{{ $t('FeaturesPage.streamingNonstreaming') }}</h3>
            <p>{{ $t('FeaturesPage.supportForBothRealtimeStreaming') }}</p>
          </div>
          <div class="feature-card">
            <div class="feature-icon">ðŸ“</div>
            <h3>{{ $t('FeaturesPage.embeddings') }}</h3>
            <p>Generate vector embeddings for text â€” ideal for semantic search, clustering, classification, and RAG (Retrieval-Augmented Generation) pipelines.</p>
          </div>
          <div class="feature-card">
            <div class="feature-icon">ðŸ”</div>
            <h3>{{ $t('FeaturesPage.functionCalling') }}</h3>
            <p>{{ $t('FeaturesPage.connectModelsToExternalTools') }}</p>
          </div>
          <div class="feature-card">
            <div class="feature-icon">ðŸ–¼ï¸</div>
            <h3>{{ $t('FeaturesPage.visionImageInput') }}</h3>
            <p>{{ $t('FeaturesPage.sendImagesToSupportedModels') }}</p>
          </div>
        </div>
      </div>

      <!-- Row 2: Platform -->
      <div class="feature-section">
        <h2>{{ $t('FeaturesPage.platform') }}</h2>
        <div class="feature-grid">
          <div class="feature-card">
            <div class="feature-icon">ðŸ”</div>
            <h3>{{ $t('FeaturesPage.apiKeyManagement') }}</h3>
            <p>{{ $t('FeaturesPage.createScopeAndRevokeApi') }}</p>
          </div>
          <div class="feature-card">
            <div class="feature-icon">ðŸ“Š</div>
            <h3>{{ $t('FeaturesPage.usageAnalytics') }}</h3>
            <p>Real-time visibility into your token consumption, request volume, and cost â€” broken down by model, time period, and API key.</p>
          </div>
          <div class="feature-card">
            <div class="feature-icon">ðŸ’°</div>
            <h3>{{ $t('FeaturesPage.transparentPricing') }}</h3>
            <p>{{ $t('FeaturesPage.payOnlyForWhatYou') }}</p>
          </div>
          <div class="feature-card">
            <div class="feature-icon">ðŸŽ¯</div>
            <h3>{{ $t('FeaturesPage.rateLimitingQuotas') }}</h3>
            <p>{{ $t('FeaturesPage.understandYourPlanLimitsAt') }}</p>
          </div>
          <div class="feature-card">
            <div class="feature-icon">ðŸš€</div>
            <h3>{{ $t('FeaturesPage.fastInference') }}</h3>
            <p>{{ $t('FeaturesPage.optimizedInferencePipelineWithIntelligent') }}</p>
          </div>
          <div class="feature-card">
            <div class="feature-icon">ðŸŒ</div>
            <h3>{{ $t('FeaturesPage.vietnamesefirst') }}</h3>
            <p>{{ $t('FeaturesPage.modelsOptimizedForVietnameseLanguage') }}</p>
          </div>
        </div>
      </div>

      <!-- Row 3: Developer Experience -->
      <div class="feature-section">
        <h2>{{ $t('FeaturesPage.developerExperience') }}</h2>
        <div class="feature-grid">
          <div class="feature-card">
            <div class="feature-icon">ðŸ“–</div>
            <h3>{{ $t('FeaturesPage.comprehensiveDocs') }}</h3>
            <p>{{ $t('FeaturesPage.detailedApiReferenceQuickstartGuides') }}</p>
          </div>
          <div class="feature-card">
            <div class="feature-icon">ðŸ› ï¸</div>
            <h3>{{ $t('FeaturesPage.openclawIntegration') }}</h3>
            <p>{{ $t('FeaturesPage.oneclickSetupToConnectOpenclaw') }}</p>
          </div>
          <div class="feature-card">
            <div class="feature-icon">ðŸ“¥</div>
            <h3>{{ $t('FeaturesPage.sdkSupport') }}</h3>
            <p>{{ $t('FeaturesPage.useAnyOpenaicompatibleSdkPython') }}</p>
          </div>
          <div class="feature-card">
            <div class="feature-icon">ðŸ§ª</div>
            <h3>{{ $t('FeaturesPage.playgroundComingSoon') }}</h3>
            <p>{{ $t('FeaturesPage.testModelsInteractivelyInYour') }}</p>
          </div>
          <div class="feature-card">
            <div class="feature-icon">ðŸ“„</div>
            <h3>{{ $t('FeaturesPage.invoiceBillingApi') }}</h3>
            <p>{{ $t('FeaturesPage.programmaticallyAccessYourBillingData') }}</p>
          </div>
          <div class="feature-card">
            <div class="feature-icon">ðŸ””</div>
            <h3>{{ $t('FeaturesPage.webhookAlertsComingSoon') }}</h3>
            <p>{{ $t('FeaturesPage.receiveRealtimeNotificationsForUsage') }}</p>
          </div>
        </div>
      </div>

      <!-- Row 4: Enterprise -->
      <div class="feature-section">
        <h2>{{ $t('FeaturesPage.enterprise') }}</h2>
        <div class="feature-grid">
          <div class="feature-card enterprise">
            <div class="feature-icon">ðŸ›¡ï¸</div>
            <h3>{{ $t('FeaturesPage.dataPrivacy') }}</h3>
            <p>{{ $t('FeaturesPage.yourDataStaysYoursOpt') }}</p>
          </div>
          <div class="feature-card enterprise">
            <div class="feature-icon">ðŸ”’</div>
            <h3>{{ $t('FeaturesPage.encryption') }}</h3>
            <p>{{ $t('FeaturesPage.endtoendEncryptionInTransitTls') }}</p>
          </div>
          <div class="feature-card enterprise">
            <div class="feature-icon">ðŸ¤</div>
            <h3>{{ $t('FeaturesPage.dedicatedSupport') }}</h3>
            <p>{{ $t('FeaturesPage.prioritySupportWithSlasFor') }}</p>
          </div>
          <div class="feature-card enterprise">
            <div class="feature-icon">âš¡</div>
            <h3>{{ $t('FeaturesPage.customDeployment') }}</h3>
            <p>{{ $t('FeaturesPage.needDedicatedInfrastructureWeOffer') }}</p>
          </div>
        </div>
      </div>
    </section>

    <footer class="site-footer document-footer">
      <span class="footer-links">
        <router-link to="/terms-of-use">{{ $t('FeaturesPage.termsOfService') }}</router-link>
        &middot;
        <router-link to="/privacy-policy">{{ $t('FeaturesPage.privacyPolicy') }}</router-link>
        &middot;
        <router-link to="/about">{{ $t('FeaturesPage.about') }}</router-link>
      </span>
      <span>Copyright 2026 &copy; <a href="https://minhtue.vn" target="_blank" rel="noopener">{{ $t('FeaturesPage.minhTueTradingInvestmentJsc') }}</a></span>
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
