<template>
  <div class="legal-page">
    <header class="legal-header">
      <router-link to="/" class="back-link">← Back to Console</router-link>
      <h1>{{ $t('AboutPage.aboutTueTueConsole') }}</h1>
    </header>

    <section class="legal-body about-body">
      <div class="about-intro">
        <img src="../assets/Tuetue-ai-2m.jpg" alt="Tuệ Tuệ" class="about-logo" />
        <p>
          <strong>{{ $t('AboutPage.tueTue_1') }}</strong> is an AI platform developed by
          <strong>{{ $t('TermsOfUsePage.minhTueTradingInvestmentJoint_1') }}</strong> — a Vietnamese enterprise
          with deep roots in manufacturing, technology, and innovation.
        </p>
      </div>

      <h2>{{ $t('AboutPage.aboutMinhTue') }}</h2>
      <p>
        Founded in 2022, Minh Tue Trading Investment Joint Stock Company (Enterprise Code:
        0110148062) is headquartered at Lot 29, Vinh Hung Ward, Hoang Mai District, Hanoi,
        Vietnam. Our manufacturing facilities span over 22,000 m² in Lang Son Province,
        producing high-quality wood chips, wood pallet blanks, and compound plastic granules
        (PP, ABS, PC bases) for FDI enterprises and export markets.
      </p>
      <p>
        With a commitment to quality, innovation, and customer satisfaction, Minh Tue has grown
        rapidly — expanding from 9 production lines toward a goal of 50 lines, and from 12
        employees toward 60 within 5 years. Our motto: <em>"Giá trị trên tay bạn!"</em>
        (Value in your hands!).
      </p>

      <h2>{{ $t('AboutPage.meetTueTue') }}</h2>
      <p>
        <strong>{{ $t('AboutPage.tueTue_1') }}</strong> is the digital soul of Minh Tue — an AI platform built to
        democratize access to intelligent technology for Vietnamese businesses and developers.
        Named with the Vietnamese word "Tuệ" (wisdom, intelligence), Tue Tue embodies our belief
        that AI should be accessible, ethical, and culturally attuned to Vietnamese users.
      </p>
      <p>
        The Tue Tue API provides OpenAI-compatible endpoints for large language models, embedding
        models, and inference services — powered by state-of-the-art open-source and proprietary
        models, running on infrastructure optimized for Vietnamese language and business contexts.
      </p>

      <h2>{{ $t('AboutPage.ourMission') }}</h2>
      <p>
        We believe that artificial general intelligence (AGI) should benefit everyone. Our mission
        is to build AI tools that help Vietnamese businesses learn, create, and solve problems —
        from startups to enterprises. We are committed to:
      </p>
      <ul>
        <li><strong>Accessibility:</strong> Making AI affordable and easy to use for Vietnamese developers and businesses;</li>
        <li><strong>Vietnamese-first:</strong> Optimizing models for Vietnamese language and cultural context;</li>
        <li><strong>Privacy & Security:</strong> Handling data with care, in full compliance with Vietnamese law;</li>
        <li><strong>Open Ecosystem:</strong> Supporting open-source models and giving developers choice.</li>
      </ul>

      <h2>{{ $t('AboutPage.ourTeam') }}</h2>
      <p>
        Tue Tue is built by a passionate team of AI researchers, software engineers, and product
        designers — united by a shared vision of bringing world-class AI capabilities to Vietnam.
        We are headquartered in Hanoi, with team members across Vietnam and internationally.
      </p>

      <h2>{{ $t('AboutPage.contact') }}</h2>
      <p>
        <strong>{{ $t('TermsOfUsePage.minhTueTradingInvestmentJoint_1') }}</strong><br>
        No 15 179/187/26, Lot 29, Vinh Hung Ward, Hoang Mai District, Hanoi, Vietnam<br>
        Email: <a href="mailto:info@minhtue.vn">info@minhtue.vn</a><br>
        Phone: 0981.123.789 – 0246.3247.8999<br>
        Enterprise Code: 0110148062<br>
        Website: <a href="https://minhtue.vn" target="_blank" rel="noopener">minhtue.vn</a><br>
        API Console: <a href="https://console.tuetue.vn">console.tuetue.vn</a>
      </p>

      <div class="about-factories">
        <h3>{{ $t('AboutPage.manufacturingProduction') }}</h3>
        <p>
          Ba Nang, Cai Kinh Commune, Huu Lung District, Lang Son Province<br>
          Enterprise Code: 0110148062-001<br>
          Phone: 0981.123.789 – 0246.3247.8999
        </p>
      </div>
    </section>

    <footer class="site-footer document-footer">
      <span>Copyright 2026 &copy; <a href="https://minhtue.vn" target="_blank" rel="noopener">{{ $t('TermsOfUsePage.minhTueTradingInvestmentJsc') }}</a></span>
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
  max-width: 820px;
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
.legal-body {
  max-width: 820px;
  margin: 0 auto;
  padding: 40px;
  border-radius: 28px;
  border: 1px solid var(--border);
  background: var(--bg-card);
  box-shadow: var(--shadow);
}
.about-body p {
  color: var(--text-secondary);
  line-height: 1.7;
  margin: 0 0 18px;
}
.about-body h2 {
  margin: 36px 0 14px;
  font-size: 22px;
  letter-spacing: -0.02em;
  color: var(--text-primary);
}
.about-body h2:first-of-type {
  margin-top: 0;
}
.about-body h3 {
  margin: 24px 0 10px;
  font-size: 17px;
  color: var(--text-primary);
}
.about-body ul {
  padding-left: 24px;
  margin: 0 0 18px;
}
.about-body li {
  color: var(--text-secondary);
  line-height: 1.7;
  margin-bottom: 8px;
}
.about-body strong {
  color: var(--text-primary);
}
.about-intro {
  display: flex;
  align-items: flex-start;
  gap: 28px;
  margin-bottom: 8px;
}
.about-logo {
  width: 80px;
  height: 80px;
  object-fit: contain;
  border-radius: 20px;
  flex-shrink: 0;
}
.about-intro p {
  margin: 0;
}
.about-factories {
  margin-top: 28px;
  padding: 20px;
  border-radius: 18px;
  background: var(--bg-subtle);
  border: 1px solid var(--border);
}
.about-factories h3 {
  margin-top: 0;
}
.about-factories p {
  margin: 0;
  font-size: 14px;
}
.document-footer {
  position: relative;
  bottom: auto;
  left: auto;
  text-align: center;
  margin-top: 32px;
  padding-bottom: 12px;
}
@media (max-width: 768px) {
  .legal-page { padding: 14px; }
  .legal-body { padding: 24px; }
  .legal-header h1 { font-size: 28px; }
  .about-intro { flex-direction: column; align-items: center; text-align: center; }
}
</style>
