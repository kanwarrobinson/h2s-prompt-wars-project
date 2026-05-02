import { storeToRefs } from 'pinia'
import { useAuthStore } from '@/stores/auth'

export function useAuth() {
  const authStore = useAuthStore()
  const {
    firebaseUser,
    profile,
    token,
    loading,
    isAuthenticated,
    displayName,
    avatarUrl,
  } = storeToRefs(authStore)

  return {
    user: firebaseUser,
    profile,
    token,
    loading,
    isAuthenticated,
    displayName,
    avatarUrl,
    loginWithGoogle: authStore.loginWithGoogle,
    logout: authStore.logout,
  }
}
