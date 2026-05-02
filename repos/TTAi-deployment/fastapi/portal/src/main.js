import { createApp } from 'vue'
import { createRouter, createWebHashHistory } from 'vue-router'
import './style.css'
import App from './App.vue'
import i18n from './i18n/index.js'
import LandingPage from './pages/LandingPage.vue'
import LoginPage from './pages/LoginPage.vue'
import SignupPage from './pages/SignupPage.vue'
import PortalLayout from './components/PortalLayout.vue'
import OverviewPage from './pages/OverviewPage.vue'
import ApiKeysPage from './pages/ApiKeysPage.vue'
import UsagePage from './pages/UsagePage.vue'
import BillingPage from './pages/BillingPage.vue'
import LimitsPage from './pages/LimitsPage.vue'
import DocsPage from './pages/DocsPage.vue'
import ProfilePage from './pages/ProfilePage.vue'
import OpenClawSetupPage from './pages/OpenClawSetupPage.vue'
import OpenClawBundlesPage from './pages/OpenClawBundlesPage.vue'
import OpenClawPresetsPage from './pages/OpenClawPresetsPage.vue'
import TermsOfUsePage from './pages/TermsOfUsePage.vue'
import PrivacyPolicyPage from './pages/PrivacyPolicyPage.vue'
import AboutPage from './pages/AboutPage.vue'
import FeaturesPage from './pages/FeaturesPage.vue'
import HelpPage from './pages/HelpPage.vue'
import QuickStartPage from './pages/QuickStartPage.vue'
import GuidePage from './pages/GuidePage.vue'
import FaqPage from './pages/FaqPage.vue'
import ContactPage from './pages/ContactPage.vue'

const router = createRouter({
  history: createWebHashHistory('/'),
  routes: [
    { path: '/', name: 'landing', component: LandingPage },
    { path: '/login', name: 'login', component: LoginPage },
    { path: '/signup', name: 'signup', component: SignupPage },
    {
      path: '/dashboard',
      component: PortalLayout,
      children: [
        { path: '', name: 'dashboard-overview', component: OverviewPage },
        { path: 'api-keys', name: 'dashboard-api-keys', component: ApiKeysPage },
        { path: 'usage', name: 'dashboard-usage', component: UsagePage },
        { path: 'billing', name: 'dashboard-billing', component: BillingPage },
        { path: 'limits', name: 'dashboard-limits', component: LimitsPage },
        { path: 'docs', name: 'dashboard-docs', component: DocsPage },
        { path: 'integrations', name: 'dashboard-integrations', component: OpenClawSetupPage },
        { path: 'integrations/bundles', name: 'dashboard-bundles', component: OpenClawBundlesPage },
        { path: 'integrations/presets', name: 'dashboard-presets', component: OpenClawPresetsPage },
        { path: 'profile', name: 'dashboard-profile', component: ProfilePage },
      ],
    },
    { path: '/terms-of-use', name: 'terms-of-use', component: TermsOfUsePage },
    { path: '/privacy-policy', name: 'privacy-policy', component: PrivacyPolicyPage },
    { path: '/features', name: 'features', component: FeaturesPage },
    { path: '/help', name: 'help', component: HelpPage },
    { path: '/start', name: 'quickstart', component: QuickStartPage },
    { path: '/guide', name: 'guide', component: GuidePage },
    { path: '/faq', name: 'faq', component: FaqPage },
    { path: '/contact', name: 'contact', component: ContactPage },
    { path: '/about', name: 'about', component: AboutPage },
  ],
})

createApp(App).use(i18n).use(router).mount('#app')
