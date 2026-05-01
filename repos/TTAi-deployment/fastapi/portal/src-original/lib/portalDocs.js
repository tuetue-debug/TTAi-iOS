import { portalFetch } from './auth'

export async function getPortalDocs() {
  return portalFetch('/portal-api/docs', { method: 'GET' })
}

export async function getPortalProfile() {
  return portalFetch('/portal-api/profile', { method: 'GET' })
}

export async function updatePortalProfile(form) {
  return portalFetch('/portal-api/profile', {
    method: 'PUT',
    body: JSON.stringify(form),
  })
}
