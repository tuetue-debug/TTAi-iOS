<template>
  <div class="legal-page">
    <header class="legal-header">
      <router-link to="/" class="back-link">â† Back to Console</router-link>
      <h1>{{ $t('TermsOfUsePage.termsOfService') }}</h1>
      <p class="legal-effective">{{ $t('TermsOfUsePage.lastUpdatedApril302026') }}</p>
    </header>

    <section class="legal-body">
      <p>
        These Terms of Service ("Terms") govern your access to and use of the Tue Tue API platform,
        website, applications, and related services (collectively, the "Services") operated by
        <strong>{{ $t('TermsOfUsePage.minhTueTradingInvestmentJoint') }}</strong> ("Minh Tue", "we", "us", or "our"),
        a company duly organized under the laws of the Socialist Republic of Vietnam
        (Enterprise Code: 0110148062), with registered address at No 15 179/187/26, Lot 29, Vinh Hung Ward,
        Hoang Mai District, Hanoi, Vietnam.
      </p>

      <p>
        By accessing or using the Services, you agree to be bound by these Terms. If you do not
        agree, you must not access or use the Services.
      </p>

      <h2>{{ $t('TermsOfUsePage.accountRegistrationAndEligibility') }}</h2>
      <p>
        You must be at least 18 years old (or the age of majority in your jurisdiction) to create
        an account. If you are under 18, you must have parental or guardian consent. You represent
        that all registration information you provide is accurate, current, and complete. You are
        responsible for safeguarding your account credentials and for all activities under your
        account. Notify us immediately at <a href="mailto:info@minhtue.vn">{{ $t('TermsOfUsePage.infominhtuevn') }}</a>
        of any unauthorized use.
      </p>
      <p>
        We reserve the right to refuse service, terminate accounts, or change pricing at our
        sole discretion, subject to applicable Vietnamese law (including the Law on Information
        Technology 2006 and Decree 72/2013/ND-CP on Internet services).
      </p>

      <h2>{{ $t('TermsOfUsePage.serviceDescription') }}</h2>
      <p>
        Tue Tue API provides artificial intelligence model access, including but not limited to
        large language models (LLMs), embedding models, and inference APIs. The Services are
        provided on an "as is" and "as available" basis. We continuously improve our models
        and may modify, suspend, or discontinue any aspect of the Services at any time with
        reasonable notice.
      </p>

      <h2>{{ $t('TermsOfUsePage.apiUsageAndRateLimits') }}</h2>
      <p>
        Access to the API is governed by your subscription plan. Each plan specifies rate limits,
        quota, and pricing. Exceeding allocated limits may result in throttling or suspension.
        You must not:
      </p>
      <ul>
        <li>{{ $t('TermsOfUsePage.useTheApiInManner') }}</li>
        <li>{{ $t('TermsOfUsePage.attemptToReverseEngineerDecompile') }}</li>
        <li>{{ $t('TermsOfUsePage.useTheApiForAny') }}</li>
        <li>{{ $t('TermsOfUsePage.interfereWithOrDisruptThe') }}</li>
      </ul>

      <h2>{{ $t('TermsOfUsePage.userContentAndData') }}</h2>
      <p>
        You retain all rights to content you input into the Services ("Your Content"). By submitting
        Your Content, you grant us a worldwide, royalty-free license to use, reproduce, and process
        Your Content solely for the purpose of providing and improving the Services. We implement
        technical and organizational measures to protect Your Content in accordance with
        Vietnamese Law on Cybersecurity (Law No. 24/2018/QH14) and Decree 13/2023/ND-CP on
        Personal Data Protection.
      </p>
      <p>
        <strong>{{ $t('TermsOfUsePage.dataRetention') }}</strong> We retain Your Content as long as necessary to provide
        the Services. You may delete your conversations through your account settings. Deleted
        content is removed from active systems within 30 days, subject to legal hold obligations.
      </p>
      <p>
        <strong>{{ $t('TermsOfUsePage.training') }}</strong> By default, we may use Your Content to improve our models. You
        can opt out of training via your account settings. Enterprise API customers are never
        used for training by default.
      </p>

      <h2>{{ $t('TermsOfUsePage.acceptableUsePolicy') }}</h2>
      <p>{{ $t('TermsOfUsePage.youAgreeNotToUse') }}</p>
      <ul>
        <li>{{ $t('TermsOfUsePage.generateDistributeOrPromoteIllegal') }}</li>
        <li>{{ $t('TermsOfUsePage.harassAbuseOrHarmOthers') }}</li>
        <li>{{ $t('TermsOfUsePage.impersonateAnyPersonOrEntity') }}</li>
        <li>{{ $t('TermsOfUsePage.violateIntellectualPropertyRights') }}</li>
        <li>{{ $t('TermsOfUsePage.distributeMalwareVirusesOrOther') }}</li>
        <li>{{ $t('TermsOfUsePage.engageInAutomatedScrapingOr') }}</li>
        <li>Violate any applicable law or regulation, including Decree 72/2013/ND-CP and
            Circular 38/2016/TT-BTTTT on information security.</li>
      </ul>

      <h2>{{ $t('TermsOfUsePage.intellectualProperty') }}</h2>
      <p>
        The Services, including but not limited to the Tue Tue API platform, user interface,
        brand assets, logo, and "Tue Tue" name, are the intellectual property of Minh Tue Trading
        Investment Joint Stock Company and are protected by Vietnamese and international
        intellectual property laws. You may not copy, modify, distribute, or create derivative
        works without our prior written consent.
      </p>
      <p>
        The output generated by our AI models (the "Output") is provided to you on a non-exclusive,
        non-transferable basis. To the extent permitted by law, we assign to you all rights to
        the Output. We make no warranty regarding the originality or non-infringement of Output.
      </p>

      <h2>{{ $t('TermsOfUsePage.feesAndPayment') }}</h2>
      <p>
        Fees are calculated based on usage as specified in your plan. All fees are exclusive of
        applicable taxes, including VAT. Payments are due according to your billing cycle. Late
        payments may result in service suspension. We may change pricing with 30 days' notice.
      </p>

      <h2>{{ $t('TermsOfUsePage.privacy') }}</h2>
      <p>
        Your privacy is important to us. Please refer to our
        <router-link to="/privacy-policy">{{ $t('TermsOfUsePage.privacyPolicy') }}</router-link> for information on how
        we collect, use, and protect your personal data, in compliance with Decree 13/2023/ND-CP
        on Personal Data Protection and other applicable Vietnamese laws.
      </p>

      <h2>{{ $t('TermsOfUsePage.limitationOfLiability') }}</h2>
      <p>
        To the maximum extent permitted by Vietnamese law (including the Civil Code 2015 and the
        Law on Protection of Consumer Rights 2010), Minh Tue shall not be liable for any indirect,
        incidental, special, consequential, or punitive damages arising out of or relating to your
        use of the Services. Our total liability for any claim shall not exceed the amount you
        have paid us in the 12 months preceding the claim.
      </p>

      <h2>{{ $t('TermsOfUsePage.10AiOutputAccuracy') }}</h2>
      <p>
        AI models generate responses by predicting likely text based on input. Output may contain
        inaccuracies, hallucinations, or outdated information. You should independently verify
        critical information. We are not responsible for decisions made based on Output. The
        Services are not intended for use in high-stakes domains such as medical diagnosis, legal
        advice, financial planning, or safety-critical systems.
      </p>

      <h2>{{ $t('TermsOfUsePage.11Termination') }}</h2>
      <p>
        Either party may terminate these Terms at any time. We may suspend or terminate your
        access to the Services if you materially breach these Terms. Upon termination, your
        right to use the Services ceases immediately. Sections 4 (User Content), 6 (Intellectual
        Property), 9 (Limitation of Liability), and 12 (Governing Law) survive termination.
      </p>

      <h2>{{ $t('TermsOfUsePage.12GoverningLawAndDispute') }}</h2>
      <p>
        These Terms are governed by the laws of the Socialist Republic of Vietnam. Any disputes
        arising out of or relating to these Terms shall be resolved through amicable negotiation
        first. If negotiation fails, disputes shall be referred to the competent court of
        Hoang Mai District, Hanoi, Vietnam. For consumers, you may also seek resolution through
        the Vietnam Competition and Consumer Authority.
      </p>

      <h2>{{ $t('TermsOfUsePage.13ChangesToTheseTerms') }}</h2>
      <p>
        We may update these Terms from time to time. Material changes will be communicated via
        email or through the Service at least 30 days before they take effect. Your continued
        use after the effective date constitutes acceptance of the updated Terms.
      </p>

      <h2>{{ $t('TermsOfUsePage.14Contact') }}</h2>
      <p>
        For questions about these Terms, please contact us at:<br>
        <strong>{{ $t('TermsOfUsePage.minhTueTradingInvestmentJoint') }}</strong><br>
        No 15 179/187/26, Lot 29, Vinh Hung Ward, Hoang Mai District, Hanoi, Vietnam<br>
        Email: <a href="mailto:info@minhtue.vn">{{ $t('TermsOfUsePage.infominhtuevn') }}</a><br>
        Enterprise Code: 0110148062<br>
        Website: <a href="https://minhtue.vn" target="_blank" rel="noopener">{{ $t('TermsOfUsePage.minhtuevn') }}</a>
      </p>
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
.legal-effective {
  color: var(--text-muted);
  font-size: 14px;
  margin: 0;
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
.legal-body p {
  color: var(--text-secondary);
  line-height: 1.7;
  margin: 0 0 18px;
}
.legal-body h2 {
  margin: 36px 0 14px;
  font-size: 22px;
  letter-spacing: -0.02em;
  color: var(--text-primary);
}
.legal-body h2:first-of-type {
  margin-top: 0;
}
.legal-body ul {
  padding-left: 24px;
  margin: 0 0 18px;
}
.legal-body li {
  color: var(--text-secondary);
  line-height: 1.7;
  margin-bottom: 8px;
}
.legal-body strong {
  color: var(--text-primary);
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
}
</style>
