const defaultHeaders = {
  'Content-Type': 'application/json',
}

export async function portalFetch(path, options = {}) {
  const response = await fetch(path, {
    credentials: 'include',
    headers: {
      ...defaultHeaders,
      ...(options.headers || {}),
    },
    ...options,
  })

  const isJson = response.headers.get('content-type')?.includes('application/json')
  const payload = isJson ? await response.json().catch(() => ({})) : null

  if (!response.ok) {
    throw new Error(payload?.detail || payload?.message || `Request failed: ${response.status}`)
  }

  return payload
}

export async function signup(form) {
  return portalFetch('/auth/signup', {
    method: 'POST',
    body: JSON.stringify(form),
  })
}

export async function login(form) {
  return portalFetch('/auth/login', {
    method: 'POST',
    body: JSON.stringify(form),
  })
}

export async function logout() {
  return portalFetch('/auth/logout', {
    method: 'POST',
  })
}

export async function getCurrentUser() {
  return portalFetch('/auth/me', {
    method: 'GET',
  })
}
