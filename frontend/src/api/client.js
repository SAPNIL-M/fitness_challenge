import axios from 'axios'
import { getAccessToken } from '../utils/currentUser'

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

// ─── Request Interceptor ─────────────────────────────────────
// Automatically attaches the stored access token, if one exists, to
// every outgoing request. Routes that don't require auth (leaderboard,
// dashboard, register, login) simply ignore an Authorization header
// they don't check for — only routes that declare the auth dependency
// (currently just POST /activities) actually verify it.

api.interceptors.request.use(
  (config) => {
    const token = getAccessToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
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

export const loginUser = (payload) =>
  api.post('/users/login', payload)

export const getUserDashboard = (userId) =>
  api.get(`/users/${userId}/dashboard`)

// ─── Activity Endpoints ──────────────────────────────────────

export const logActivity = (payload) =>
  api.post('/activities', payload)

// ─── Leaderboard Endpoints ───────────────────────────────────

export const getLeaderboard = () =>
  api.get('/activities/leaderboard')
