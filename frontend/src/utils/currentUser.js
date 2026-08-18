const STORAGE_KEY = 'fc_current_user'

export function getCurrentUser() {
  const raw = localStorage.getItem(STORAGE_KEY)
  if (!raw) return null

  try {
    return JSON.parse(raw)
  } catch {
    return null
  }
}

export function setCurrentUser(userId, name, accessToken) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify({ userId, name, accessToken }))
}

export function clearCurrentUser() {
  localStorage.removeItem(STORAGE_KEY)
}

export function getAccessToken() {
  return getCurrentUser()?.accessToken ?? null
}
