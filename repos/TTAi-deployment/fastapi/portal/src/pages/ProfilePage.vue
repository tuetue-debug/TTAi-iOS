<script setup>
import { onMounted, reactive, ref } from 'vue'
import { getPortalProfile, updatePortalProfile } from '../lib/portalDocs'
import { getSocialProviders } from '../lib/portalSocial'

const loading = ref(true)
const saving = ref(false)
const error = ref('')
const success = ref('')
const profile = ref(null)
const providers = ref([])

const form = reactive({
  name: '',
  email: '',
})

onMounted(async () => {
  try {
    const [profileRes, providersRes] = await Promise.all([
      getPortalProfile(),
      getSocialProviders(),
    ])
    profile.value = profileRes.user
    providers.value = providersRes.items || []
    form.name = profileRes.user.name || ''
    form.email = profileRes.user.email || ''
  } catch (err) {
    error.value = err?.message || 'Failed to load profile'
  } finally {
    loading.value = false
  }
})

async function handleSave() {
  error.value = ''
  success.value = ''
  saving.value = true
  try {
    const payload = await updatePortalProfile({
      name: form.name,
      email: form.email,
    })
    profile.value = payload.user
    success.value = 'Profile updated'
  } catch (err) {
    error.value = err?.message || 'Profile update failed'
  } finally {
    saving.value = false
  }
}

function handleLinkProvider(provider) {
  window.location.href = `/auth/${provider}/start`
}
</script>

<template>
  <section class="single-column-grid profile-shell-page">
    <div class="page-intro">
      <h3>{{ $t('ProfilePage.accountSettings') }}</h3>
      <p>{{ $t('ProfilePage.manageYourPortalProfileAnd') }}</p>
    </div>

    <div v-if="loading" class="empty-state">Loading profile…</div>
    <div v-else class="single-column-grid">
      <article class="panel-subtle">
        <form class="auth-form" @submit.prevent="handleSave">
          <label>
            <span>{{ $t('ProfilePage.fullName') }}</span>
            <input v-model="form.name" type="text" placeholder="Your name" />
          </label>
          <label>
            <span>{{ $t('ProfilePage.email') }}</span>
            <input v-model="form.email" type="email" placeholder="you@company.com" />
          </label>
          <button class="primary-btn full" :disabled="saving">
            {{ saving ? 'Saving…' : 'Save changes' }}
          </button>
          <p v-if="error" class="form-error">{{ error }}</p>
          <p v-if="success" class="form-success">{{ success }}</p>
        </form>
      </article>

      <article class="panel-subtle">
        <h4 style="margin-top: 0; margin-bottom: 12px;">{{ $t('ProfilePage.socialAccounts') }}</h4>
        <p style="margin-bottom: 16px; color: #64748b; font-size: 14px;">{{ $t('ProfilePage.linkYourGoogleGithubOr') }}</p>
        <div class="social-providers">
          <div v-for="item in providers" :key="item.provider" class="provider-item">
            <div>
              <div class="provider-name">{{ item.provider }}</div>
              <div class="provider-status">{{ item.status === 'linked' ? 'Linked' : 'Available' }}</div>
            </div>
            <button
              class="ghost-btn"
              :disabled="item.status === 'linked'"
              @click="handleLinkProvider(item.provider)"
            >
              {{ item.status === 'linked' ? 'Linked' : 'Link' }}
            </button>
          </div>
        </div>
      </article>
    </div>
  </section>
</template>
