<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { RouterView } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import Sidebar from '@/components/shared/Sidebar.vue'
import AppHeader from '@/components/shared/AppHeader.vue'

const authStore = useAuthStore()
const route = useRoute()
const sidebarOpen = ref(false)

const isPublicRoute = () => route.meta.public === true

onMounted(() => {
  authStore.init()
})
</script>

<template>
  <div class="min-h-screen bg-gray-50 dark:bg-surface-dark font-sans">
    <!-- Full-screen loading spinner while auth initializes -->
    <div
      v-if="authStore.loading"
      class="fixed inset-0 flex items-center justify-center bg-white dark:bg-surface-dark z-50"
    >
      <div class="flex flex-col items-center gap-4">
        <div class="w-12 h-12 bg-brand-500 rounded-2xl flex items-center justify-center shadow-lg">
          <span class="text-white text-2xl font-bold">D</span>
        </div>
        <svg
          class="animate-spin h-6 w-6 text-brand-500"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            class="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            stroke-width="4"
          />
          <path
            class="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
          />
        </svg>
      </div>
    </div>

    <!-- Public layout (login page, etc.) -->
    <template v-else-if="isPublicRoute()">
      <RouterView />
    </template>

    <!-- App layout (authenticated) -->
    <template v-else>
      <div class="flex h-screen overflow-hidden">
        <Sidebar />
        <div class="flex flex-col flex-1 min-w-0 overflow-hidden">
          <AppHeader @toggle-sidebar="sidebarOpen = !sidebarOpen" />
          <main class="flex-1 overflow-hidden">
            <RouterView />
          </main>
        </div>
      </div>
    </template>
  </div>
</template>
