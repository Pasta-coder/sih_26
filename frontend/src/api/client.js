import axios from 'axios'

// The Cloudflare Quick Tunnel URL changes every time the service restarts.
// Hardcoding the latest tunnel URL here to fix the login issue immediately.
const baseURL = 'https://moreover-anybody-ware-thru.trycloudflare.com/api'

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
