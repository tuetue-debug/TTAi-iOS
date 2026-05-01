import { portalFetch } from './auth'

export async function getSocialProviders() {
  return portalFetch('/portal-api/social-auth/providers', { method: 'GET' })
}

export async function linkSocialProvider(form) {
  return portalFetch('/portal-api/social-auth/link', {
    method: 'POST',
    body: JSON.stringify(form),
  })
}
