const BASE = ''

async function apiFetch(path, options = {}) {
  const res = await fetch(path, {
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }
  return res.json()
}

export async function getCurrentUser() {
  return apiFetch('/auth/me')
}

export async function login(email, password) {
  return apiFetch('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  })
}

export async function logout() {
  return apiFetch('/auth/logout', { method: 'POST' })
}

// Guest session ID stored in localStorage
export function getGuestId() {
  let id = localStorage.getItem('ttai_guest_id')
  if (!id) {
    id = crypto.randomUUID()
    localStorage.setItem('ttai_guest_id', id)
  }
  return id
}
