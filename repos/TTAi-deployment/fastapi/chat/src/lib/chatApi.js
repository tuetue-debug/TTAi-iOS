import { getGuestId } from './auth'

function guestHeaders() {
  return { 'X-Guest-Session': getGuestId() }
}

async function apiFetch(path, options = {}) {
  const res = await fetch(path, {
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...guestHeaders(),
      ...options.headers,
    },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }
  return res.json()
}

// Models
export async function getModels() {
  return apiFetch('/chat-api/models')
}

// Conversations
export async function getConversations() {
  return apiFetch('/chat-api/conversations')
}

export async function createConversation(model = 'qwen3:4b', projectId = null) {
  return apiFetch('/chat-api/conversations', {
    method: 'POST',
    body: JSON.stringify({ model, project_id: projectId }),
  })
}

export async function getConversationDetail(convId) {
  return apiFetch(`/chat-api/conversations/${convId}`)
}

export async function deleteConversation(convId) {
  return apiFetch(`/chat-api/conversations/${convId}`, { method: 'DELETE' })
}

// Streaming message — returns async generator yielding {type, content} objects
export async function* sendMessage(convId, content, model) {
  const res = await fetch(`/chat-api/conversations/${convId}/messages`, {
    method: 'POST',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...guestHeaders(),
    },
    body: JSON.stringify({ content, model }),
  })

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() // keep incomplete line
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        try {
          const data = JSON.parse(line.slice(6))
          yield data
        } catch {}
      }
    }
  }
}

// Guest status
export async function getGuestStatus() {
  return apiFetch('/chat-api/guest/status')
}

// Memory
export async function getMemory() {
  return apiFetch('/chat-api/memory')
}

export async function updateMemory(facts) {
  return apiFetch('/chat-api/memory', {
    method: 'PUT',
    body: JSON.stringify({ facts }),
  })
}

export async function clearMemory() {
  return apiFetch('/chat-api/memory', { method: 'DELETE' })
}

// Projects
export async function getProjects() {
  return apiFetch('/chat-api/projects')
}

export async function createProject(name, context = '') {
  return apiFetch('/chat-api/projects', {
    method: 'POST',
    body: JSON.stringify({ name, context }),
  })
}

export async function updateProject(id, data) {
  return apiFetch(`/chat-api/projects/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

export async function deleteProject(id) {
  return apiFetch(`/chat-api/projects/${id}`, { method: 'DELETE' })
}
