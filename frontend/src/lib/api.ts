import axios, { type AxiosInstance, type AxiosError } from 'axios'

const api: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8001',
  timeout: 30_000,
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('devcollab_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('devcollab_token')
      window.location.href = '/login'
    }
    if (error.response?.status === 429) {
      console.warn('Rate limited — slow down requests')
    }
    return Promise.reject(error)
  }
)

export default api

export function setAuthToken(token: string | null): void {
  if (token) {
    localStorage.setItem('devcollab_token', token)
    api.defaults.headers.common['Authorization'] = `Bearer ${token}`
  } else {
    localStorage.removeItem('devcollab_token')
    delete api.defaults.headers.common['Authorization']
  }
}
