import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  signInWithPopup,
  signOut,
  onAuthStateChanged,
  type User as FirebaseUser,
} from 'firebase/auth'
import { auth, googleProvider } from '@/lib/firebase'
import { setAuthToken } from '@/lib/api'
import api from '@/lib/api'
import type { User } from '@/types'

export const useAuthStore = defineStore('auth', () => {
  const firebaseUser = ref<FirebaseUser | null>(null)
  const profile = ref<User | null>(null)
  const token = ref<string | null>(null)
  const loading = ref(true)
  const error = ref<string | null>(null)

  const isAuthenticated = computed(() => !!firebaseUser.value)
  const displayName = computed(
    () => profile.value?.display_name ?? firebaseUser.value?.displayName ?? ''
  )
  const avatarUrl = computed(
    () => profile.value?.avatar_url ?? firebaseUser.value?.photoURL ?? null
  )

  async function loginWithGoogle(): Promise<void> {
    error.value = null
    try {
      const result = await signInWithPopup(auth, googleProvider)
      const idToken = await result.user.getIdToken()
      token.value = idToken
      setAuthToken(idToken)
      firebaseUser.value = result.user
      await _syncProfile()
    } catch (e: unknown) {
      error.value = (e as Error).message ?? 'Login failed'
      throw e
    }
  }

  async function logout(): Promise<void> {
    await signOut(auth)
    firebaseUser.value = null
    profile.value = null
    token.value = null
    setAuthToken(null)
  }

  async function refreshToken(): Promise<string | null> {
    if (!firebaseUser.value) return null
    const idToken = await firebaseUser.value.getIdToken(true)
    token.value = idToken
    setAuthToken(idToken)
    return idToken
  }

  async function _syncProfile(): Promise<void> {
    try {
      const { data } = await api.post('/api/v1/auth/login', {})
      profile.value = data
    } catch {
      // Profile sync failure is non-fatal
    }
  }

  function init(): void {
    onAuthStateChanged(auth, async (user) => {
      firebaseUser.value = user
      if (user) {
        const idToken = await user.getIdToken()
        token.value = idToken
        setAuthToken(idToken)
        await _syncProfile()
      } else {
        setAuthToken(null)
      }
      loading.value = false
    })
  }

  return {
    firebaseUser,
    profile,
    token,
    loading,
    error,
    isAuthenticated,
    displayName,
    avatarUrl,
    loginWithGoogle,
    logout,
    refreshToken,
    init,
  }
})
