<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const router = useRouter()
const isLoading = ref(false)

onMounted(() => {
  if (authStore.isAuthenticated) {
    router.replace('/dashboard')
  }
})

async function handleGoogleLogin() {
  isLoading.value = true
  try {
    await authStore.loginWithGoogle()
    router.push('/dashboard')
  } catch {
    // error is set in the store
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-surface-dark px-4">
    <div class="w-full max-w-md">
      <!-- Logo -->
      <div class="text-center mb-10">
        <div class="inline-flex items-center justify-center w-16 h-16 bg-brand-500 rounded-2xl mb-4 shadow-lg">
          <span class="text-white text-3xl font-bold">D</span>
        </div>
        <h1 class="text-3xl font-bold text-gray-900 dark:text-white">DevCollab</h1>
        <p class="mt-2 text-gray-500 dark:text-gray-400">Team collaboration, reimagined</p>
      </div>

      <!-- Card -->
      <div class="bg-white dark:bg-surface-dark-elevated rounded-2xl shadow-xl p-8">
        <h2 class="text-xl font-semibold text-gray-900 dark:text-white mb-6 text-center">
          Sign in to your workspace
        </h2>

        <!-- Error message -->
        <div
          v-if="authStore.error"
          class="mb-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg"
        >
          <p class="text-sm text-red-700 dark:text-red-400">{{ authStore.error }}</p>
        </div>

        <!-- Google Sign In -->
        <button
          :disabled="isLoading"
          class="w-full flex items-center justify-center gap-3 px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-xl text-gray-700 dark:text-gray-200 font-medium hover:bg-gray-50 dark:hover:bg-white/5 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          @click="handleGoogleLogin"
        >
          <!-- Spinner -->
          <svg
            v-if="isLoading"
            class="animate-spin h-5 w-5 text-brand-500"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path
              class="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
            />
          </svg>
          <!-- Google icon -->
          <svg v-else width="20" height="20" viewBox="0 0 48 48">
            <path fill="#FFC107" d="M43.6 20.1H42V20H24v8h11.3C33.6 32.7 29.3 36 24 36c-6.6 0-12-5.4-12-12s5.4-12 12-12c3.1 0 5.8 1.1 8 2.9l5.7-5.7C34.5 6.7 29.6 4 24 4 12.9 4 4 12.9 4 24s8.9 20 20 20c11 0 20-9 20-20 0-1.3-.1-2.7-.4-3.9z"/>
            <path fill="#FF3D00" d="M6.3 14.7l6.6 4.8C14.6 15.1 19 12 24 12c3.1 0 5.8 1.1 8 2.9l5.7-5.7C34.5 6.7 29.6 4 24 4 16.3 4 9.7 8.3 6.3 14.7z"/>
            <path fill="#4CAF50" d="M24 44c5.5 0 10.4-2.1 14.1-5.5l-6.5-5.5C29.6 35 26.9 36 24 36c-5.2 0-9.6-3.4-11.2-8H6.1C9.5 36.9 16.2 44 24 44z"/>
            <path fill="#1976D2" d="M43.6 20.1H42V20H24v8h11.3c-.8 2.3-2.3 4.3-4.3 5.7l6.5 5.5C43 35.4 44 30 44 24c0-1.3-.1-2.7-.4-3.9z"/>
          </svg>
          <span>{{ isLoading ? 'Signing in…' : 'Continue with Google' }}</span>
        </button>

        <p class="mt-6 text-center text-xs text-gray-400 dark:text-gray-500">
          By signing in, you agree to our
          <a href="#" class="text-brand-500 hover:underline">Terms</a>
          and
          <a href="#" class="text-brand-500 hover:underline">Privacy Policy</a>.
        </p>
      </div>
    </div>
  </div>
</template>
