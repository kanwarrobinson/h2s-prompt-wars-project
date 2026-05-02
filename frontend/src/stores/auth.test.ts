import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from '@/stores/auth'

vi.mock('@/lib/firebase', () => ({
  auth: {},
  googleProvider: {},
  db: {},
}))

vi.mock('@/lib/api', () => ({
  default: {
    post: vi.fn(),
    get: vi.fn(),
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() },
    },
    defaults: { headers: { common: {} } },
  },
  setAuthToken: vi.fn(),
}))

vi.mock('firebase/auth', () => ({
  signInWithPopup: vi.fn(),
  signOut: vi.fn(),
  onAuthStateChanged: vi.fn((auth, cb) => {
    cb(null)
    return vi.fn()
  }),
  getIdToken: vi.fn(async () => 'mock-token'),
}))

describe('useAuthStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('starts with loading=true and no user', () => {
    const store = useAuthStore()
    expect(store.profile).toBeNull()
    expect(store.isAuthenticated).toBe(false)
  })

  it('isAuthenticated is false when no firebase user', () => {
    const store = useAuthStore()
    expect(store.isAuthenticated).toBe(false)
  })

  it('logout clears user state', async () => {
    const { signOut } = await import('firebase/auth')
    vi.mocked(signOut).mockResolvedValueOnce(undefined)

    const store = useAuthStore()
    await store.logout()

    expect(store.profile).toBeNull()
    expect(store.token).toBeNull()
  })

  it('init subscribes to auth state changes', () => {
    const { onAuthStateChanged } = require('firebase/auth')
    const store = useAuthStore()
    store.init()
    expect(onAuthStateChanged).toHaveBeenCalled()
  })
})
