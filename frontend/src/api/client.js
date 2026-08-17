import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

// ─── Request Interceptor ─────────────────────────────────────

api.interceptors.request.use(
  (config) => config,
  (error) => Promise.reject(error)
)

// ─── Response Interceptor ────────────────────────────────────

api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const message =
      error.response?.data?.detail?.message ||
      error.response?.data?.detail ||
      error.message ||
      'An unexpected error occurred'

    return Promise.reject(new Error(message))
  }
)

// ─── User Endpoints ──────────────────────────────────────────

export const registerUser = (payload) =>
  api.post('/users/register', payload)

export const getUserDashboard = (userId) =>
  api.get(`/users/${userId}/dashboard`)

// ─── Activity Endpoints ──────────────────────────────────────

export const logActivity = (payload) =>
  api.post('/activities', payload)

// ─── Leaderboard Endpoints ───────────────────────────────────

export const getLeaderboard = () =>
  api.get('/activities/leaderboard')

