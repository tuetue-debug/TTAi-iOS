<template>
  <div class="legal-page">
    <header class="legal-header">
      <router-link to="/" class="back-link">â† Back to Console</router-link>
      <h1>{{ $t('PrivacyPolicyPage.privacyPolicy') }}</h1>
      <p class="legal-effective">{{ $t('PrivacyPolicyPage.lastUpdatedApril302026') }}</p>
    </header>

    <section class="legal-body">
      <p>
        At <strong>{{ $t('PrivacyPolicyPage.minhTueTradingInvestmentJoint') }}</strong> ("Minh Tue", "we", "us"),
        we are committed to protecting your privacy and handling your personal data with care in
        accordance with Vietnamese law, particularly <strong>Decree 13/2023/ND-CP on Personal Data
        Protection</strong>, the <strong>{{ $t('PrivacyPolicyPage.lawOnCybersecurityLawNo') }}</strong>, and
        the <strong>{{ $t('PrivacyPolicyPage.civilCode2015') }}</strong>. This Privacy Policy describes how we collect, use,
        disclose, and protect your personal data when you use the Tue Tue API platform, website,
        applications, and related services (collectively, the "Services").
      </p>

      <h2>{{ $t('PrivacyPolicyPage.whatPersonalDataWeCollect') }}</h2>

      <h3>{{ $t('PrivacyPolicyPage.11DataYouProvide') }}</h3>
      <ul>
        <li><strong>{{ $t('PrivacyPolicyPage.accountInformation') }}</strong> When you create an account, we collect your name, email address, phone number, account login credentials, date of birth (for age verification), payment information, and transaction history.</li>
        <li><strong>{{ $t('PrivacyPolicyPage.userContent') }}</strong> We collect data you input into our Services, including prompts, files, images, and other content you submit.</li>
        <li><strong>{{ $t('PrivacyPolicyPage.communicationData') }}</strong> When you contact us via email, social media, or support channels, we collect your contact information and message contents.</li>
        <li><strong>{{ $t('PrivacyPolicyPage.identityVerification') }}</strong> We may collect additional information to verify your identity or age as required by Vietnamese law.</li>
      </ul>

      <h3>{{ $t('PrivacyPolicyPage.12DataCollectedAutomatically') }}</h3>
      <ul>
        <li><strong>{{ $t('PrivacyPolicyPage.logData') }}</strong> IP address, browser type and settings, request timestamps, and how you interact with our Services.</li>
        <li><strong>{{ $t('PrivacyPolicyPage.usageData') }}</strong> Features used, actions taken, feedback provided, country, time zone, device type and operating system.</li>
        <li><strong>{{ $t('PrivacyPolicyPage.deviceInformation') }}</strong> Device name, operating system, device identifiers, and browser information.</li>
        <li><strong>{{ $t('PrivacyPolicyPage.cookies') }}</strong> We use cookies and similar technologies to operate and improve our Services. You can manage cookie preferences through your browser settings.</li>
      </ul>

      <h3>{{ $t('PrivacyPolicyPage.13DataFromOtherSources') }}</h3>
      <p>
        We may receive information from security partners (to detect fraud and abuse) and
        marketing providers (for business leads). We also collect publicly available internet
        data to develop our AI models, as permitted by applicable law.
      </p>

      <h2>{{ $t('PrivacyPolicyPage.howWeUseYourData') }}</h2>
      <p>{{ $t('PrivacyPolicyPage.weUseYourPersonalData') }}</p>
      <ul>
        <li>{{ $t('PrivacyPolicyPage.toProvideMaintainAndImprove') }}</li>
        <li>{{ $t('PrivacyPolicyPage.toDevelopAndTrainAi') }}</li>
        <li>{{ $t('PrivacyPolicyPage.toPersonalizeAndCustomizeYour') }}</li>
        <li>{{ $t('PrivacyPolicyPage.toCommunicateWithYouAbout') }}</li>
        <li>{{ $t('PrivacyPolicyPage.toDetectAndPreventFraud') }}</li>
        <li>{{ $t('PrivacyPolicyPage.toComplyWithLegalObligations') }}</li>
        <li>{{ $t('PrivacyPolicyPage.toProcessPaymentsAndManage') }}</li>
        <li>{{ $t('PrivacyPolicyPage.toConductResearchAndAnalytics') }}</li>
      </ul>

      <h2>{{ $t('PrivacyPolicyPage.legalBasisForProcessingVietnamese') }}</h2>
      <p>
        We process your personal data based on the following legal grounds under Decree 13/2023/ND-CP:
      </p>
      <ul>
        <li><strong>{{ $t('PrivacyPolicyPage.consent') }}</strong> Where you have given explicit consent for specific processing purposes;</li>
        <li><strong>{{ $t('PrivacyPolicyPage.contractualNecessity') }}</strong> Processing necessary to perform our contract with you (provide the Services);</li>
        <li><strong>{{ $t('PrivacyPolicyPage.legalObligation') }}</strong> Processing required to comply with Vietnamese laws and regulations;</li>
        <li><strong>{{ $t('PrivacyPolicyPage.legitimateInterest') }}</strong> Processing for our legitimate business interests, such as fraud prevention and service improvement, provided such interests do not override your fundamental rights.</li>
      </ul>

      <h2>{{ $t('PrivacyPolicyPage.dataDisclosure') }}</h2>
      <p>{{ $t('PrivacyPolicyPage.weMayDiscloseYourPersonal') }}</p>
      <ul>
        <li><strong>{{ $t('PrivacyPolicyPage.serviceProviders') }}</strong> To third-party vendors who assist us in operating our Services (hosting, customer support, analytics, payment processing). These providers are contractually bound to protect your data.</li>
        <li><strong>{{ $t('PrivacyPolicyPage.legalCompliance') }}</strong> To government authorities when required by Vietnamese law (including the Cybersecurity Law, criminal procedure laws, or competent court orders). We will notify you of such requests where legally permitted.</li>
        <li><strong>{{ $t('PrivacyPolicyPage.businessTransfers') }}</strong> In connection with a merger, acquisition, or sale of assets, your data may be transferred as part of the transaction.</li>
        <li><strong>{{ $t('PrivacyPolicyPage.otherUsers') }}</strong> When you choose to share content (such as conversations or API results) with other users or third parties.</li>
      </ul>
      <p>
        <strong>{{ $t('PrivacyPolicyPage.weDoNotSellYour') }}</strong> for advertising or commercial purposes.
      </p>

      <h2>{{ $t('PrivacyPolicyPage.dataRetention') }}</h2>
      <p>{{ $t('PrivacyPolicyPage.weRetainYourPersonalData') }}</p>
      <ul>
        <li><strong>{{ $t('PrivacyPolicyPage.accountData') }}</strong> Retained until you delete your account. After deletion, data is removed from active systems within 30 days.</li>
        <li><strong>{{ $t('PrivacyPolicyPage.conversationData') }}</strong> Retained according to your settings. Temporary chats are deleted within 30 days.</li>
        <li><strong>{{ $t('PrivacyPolicyPage.legalRetention') }}</strong> We may retain data longer where required by Vietnamese law (e.g., financial records for 5 years under the Accounting Law) or for fraud prevention.</li>
        <li><strong>{{ $t('PrivacyPolicyPage.anonymizedData') }}</strong> We may retain anonymized or aggregated data indefinitely for analytics and model improvement.</li>
      </ul>

      <h2>{{ $t('PrivacyPolicyPage.dataSubjectRights') }}</h2>
      <p>{{ $t('PrivacyPolicyPage.underDecree132023ndcpYouHave') }}</p>
      <ul>
        <li><strong>{{ $t('PrivacyPolicyPage.rightToBeInformed') }}</strong> To know how your data is processed;</li>
        <li><strong>{{ $t('PrivacyPolicyPage.rightToAccess') }}</strong> To request a copy of your personal data;</li>
        <li><strong>{{ $t('PrivacyPolicyPage.rightToRectification') }}</strong> To correct inaccurate or incomplete data;</li>
        <li><strong>{{ $t('PrivacyPolicyPage.rightToErasure') }}</strong> To request deletion of your personal data;</li>
        <li><strong>{{ $t('PrivacyPolicyPage.rightToRestrictProcessing') }}</strong> To limit how we process your data;</li>
        <li><strong>{{ $t('PrivacyPolicyPage.rightToDataPortability') }}</strong> To receive your data in a structured, machine-readable format;</li>
        <li><strong>{{ $t('PrivacyPolicyPage.rightToObject') }}</strong> To object to processing for marketing or other purposes;</li>
        <li><strong>{{ $t('PrivacyPolicyPage.rightToWithdrawConsent') }}</strong> To withdraw consent at any time (without affecting lawful processing before withdrawal);</li>
        <li><strong>{{ $t('PrivacyPolicyPage.rightToComplain') }}</strong> To lodge a complaint with the Ministry of Public Security or the Authority of Cybersecurity and Information Security.</li>
      </ul>
      <p>
        To exercise these rights, please visit <a href="https://privacy.tuetue.vn" target="_blank" rel="noopener">{{ $t('PrivacyPolicyPage.privacytuetuevn') }}</a>
        or email <a href="mailto:info@minhtue.vn">{{ $t('PrivacyPolicyPage.infominhtuevn') }}</a>. We will respond within the
        timeframe required by Vietnamese law (typically 30 days).
      </p>

      <h2>{{ $t('PrivacyPolicyPage.dataSecurity') }}</h2>
      <p>
        We implement appropriate technical and organizational measures to protect your personal
        data, including encryption in transit (TLS 1.3), encryption at rest, access controls,
        regular security audits, and incident response procedures. However, no system is
        completely secure. You are responsible for safeguarding your API keys and account credentials.
      </p>

      <h2>{{ $t('PrivacyPolicyPage.internationalDataTransfers') }}</h2>
      <p>
        Your data may be stored and processed on servers located in Vietnam and other jurisdictions.
        When transferring data across borders, we ensure compliance with Decree 13/2023/ND-CP
        requirements, including executing Standard Contractual Clauses (SCCs) or obtaining your
        explicit consent, and notifying the Ministry of Public Security where required.
      </p>

      <h2>{{ $t('PrivacyPolicyPage.childrensPrivacy') }}</h2>
      <p>
        Our Services are not directed to children under 13. We do not knowingly collect personal
        data from children under 13. If we discover such data, we will delete it promptly.
        Users under 18 must have parental or guardian consent to use the Services.
      </p>

      <h2>{{ $t('PrivacyPolicyPage.10AiModelTraining') }}</h2>
      <p>
        We may use your content to improve our AI models. You can opt out at any time through
        your account settings under "Data Controls." Enterprise API customers are not used for
        training by default. For more information, see our
        <router-link to="/terms-of-use">{{ $t('PrivacyPolicyPage.termsOfService') }}</router-link>.
      </p>

      <h2>{{ $t('PrivacyPolicyPage.11ChangesToThisPolicy') }}</h2>
      <p>
        We may update this Privacy Policy from time to time. We will notify you of material
        changes via email or through the Services. We encourage you to review this policy
        periodically.
      </p>

      <h2>{{ $t('PrivacyPolicyPage.12ContactUs') }}</h2>
      <p>
        If you have questions about this Privacy Policy or wish to exercise your data rights,
        please contact us at:<br><br>
        <strong>{{ $t('PrivacyPolicyPage.dataProtectionOfficerDpo') }}</strong><br>
        Minh Tue Trading Investment Joint Stock Company<br>
        No 15 179/187/26, Lot 29, Vinh Hung Ward, Hoang Mai District, Hanoi, Vietnam<br>
        Email: <a href="mailto:info@minhtue.vn">{{ $t('PrivacyPolicyPage.infominhtuevn') }}</a><br>
        Enterprise Code: 0110148062<br>
        Website: <a href="https://minhtue.vn" target="_blank" rel="noopener">{{ $t('PrivacyPolicyPage.minhtuevn') }}</a>
      </p>
    </section>

    <footer class="site-footer document-footer">
      <span>Copyright 2026 &copy; <a href="https://minhtue.vn" target="_blank" rel="noopener">{{ $t('PrivacyPolicyPage.minhTueTradingInvestmentJsc') }}</a></span>
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
.legal-body h3 {
  margin: 24px 0 10px;
  font-size: 17px;
  color: var(--text-primary);
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
