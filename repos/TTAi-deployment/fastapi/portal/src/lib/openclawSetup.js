import { portalFetch } from './auth'

export async function getOpenClawStarterPresets() {
  return portalFetch('/portal-api/openclaw/starter-presets', { method: 'GET' })
}

export async function getOpenClawSetupBundles() {
  return portalFetch('/portal-api/openclaw/setup-bundles', { method: 'GET' })
}

export async function getOpenClawSetupBundle(bundleId) {
  return portalFetch(`/portal-api/openclaw/setup-bundles/${bundleId}`, { method: 'GET' })
}

export async function createOpenClawSetupBundle(payload) {
  return portalFetch('/portal-api/openclaw/setup-bundles', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function deleteOpenClawSetupBundle(bundleId) {
  return portalFetch(`/portal-api/openclaw/setup-bundles/${bundleId}`, {
    method: 'DELETE',
  })
}

export async function previewOpenClawSetup(payload) {
  return portalFetch('/portal-api/openclaw/preview', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}
