import axios from 'axios'

// In local dev: Vite proxies /api → localhost:8000 (no env var needed)
// In production (Vercel): VITE_API_URL = https://your-app.railway.app
const baseURL = import.meta.env.VITE_API_URL
  ? `${import.meta.env.VITE_API_URL}/api`
  : '/api'

const api = axios.create({ baseURL })

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (r) => r,
  (err) => {
    // F3: a failed login returns 401 too, but redirecting reloads the app and
    // wipes the inline error message. Only redirect for authenticated calls.
    const isLoginCall = err.config?.url?.includes('/auth/login')
    if (err.response?.status === 401 && !isLoginCall) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

export default api
