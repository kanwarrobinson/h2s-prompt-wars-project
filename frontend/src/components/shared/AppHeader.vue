<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useMessageStore } from '@/stores/messages'
import { useWorkspaceStore } from '@/stores/workspace'
import Avatar from './Avatar.vue'

const emit = defineEmits<{
  toggleSidebar: []
}>()

const router = useRouter()
const authStore = useAuthStore()
const messageStore = useMessageStore()
const workspaceStore = useWorkspaceStore()

const searchQuery = ref('')
const userMenuOpen = ref(false)
const notifOpen = ref(false)

const unreadCount = computed(() => messageStore.unreadCount)

let searchTimer: ReturnType<typeof setTimeout> | null = null
function onSearch() {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    // Future: implement global search
  }, 300)
}

async function handleLogout() {
  userMenuOpen.value = false
  await authStore.logout()
  router.push('/login')
}
</script>

<template>
  <header class="h-14 bg-white dark:bg-surface-dark-elevated border-b border-gray-200 dark:border-gray-700 flex items-center px-4 gap-3 z-10">
    <!-- Hamburger (mobile) -->
    <button
      class="md:hidden p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-white/5 text-gray-500 dark:text-gray-400"
      @click="emit('toggleSidebar')"
    >
      ☰
    </button>

    <!-- Workspace name -->
    <span class="hidden md:block font-semibold text-gray-900 dark:text-white text-sm">
      {{ workspaceStore.currentWorkspace?.name ?? 'DevCollab' }}
    </span>

    <!-- Search -->
    <div class="flex-1 max-w-lg mx-auto">
      <div class="relative">
        <span class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm">🔍</span>
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Search tasks, messages, people…"
          class="w-full pl-9 pr-4 py-1.5 text-sm bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-200 placeholder-gray-400 rounded-lg border border-transparent focus:outline-none focus:ring-2 focus:ring-brand-500 focus:bg-white dark:focus:bg-surface-dark transition-colors"
          @input="onSearch"
        />
      </div>
    </div>

    <!-- Notifications -->
    <div class="relative">
      <button
        class="relative p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-white/5 text-gray-500 dark:text-gray-400 transition-colors"
        @click="notifOpen = !notifOpen"
      >
        🔔
        <span
          v-if="unreadCount > 0"
          class="absolute top-1 right-1 min-w-[16px] h-4 bg-red-500 text-white text-xs font-medium rounded-full flex items-center justify-center px-0.5"
        >
          {{ unreadCount > 99 ? '99+' : unreadCount }}
        </span>
      </button>

      <!-- Notifications panel -->
      <div
        v-if="notifOpen"
        class="absolute right-0 top-full mt-2 w-80 bg-white dark:bg-surface-dark-elevated rounded-xl shadow-xl border border-gray-200 dark:border-gray-700 py-2 z-50"
      >
        <p class="px-4 py-2 text-sm font-semibold text-gray-900 dark:text-white border-b border-gray-100 dark:border-gray-700">
          Notifications
        </p>
        <p class="px-4 py-6 text-sm text-center text-gray-400">No new notifications</p>
      </div>
    </div>

    <!-- User menu -->
    <div class="relative">
      <button
        class="flex items-center gap-2 p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-white/5 transition-colors"
        @click="userMenuOpen = !userMenuOpen"
      >
        <Avatar
          :src="authStore.avatarUrl"
          :name="authStore.displayName || 'User'"
          size="sm"
        />
      </button>

      <div
        v-if="userMenuOpen"
        class="absolute right-0 top-full mt-2 w-52 bg-white dark:bg-surface-dark-elevated rounded-xl shadow-xl border border-gray-200 dark:border-gray-700 py-1 z-50"
      >
        <div class="px-4 py-2 border-b border-gray-100 dark:border-gray-700">
          <p class="text-sm font-semibold text-gray-900 dark:text-white truncate">
            {{ authStore.displayName }}
          </p>
          <p class="text-xs text-gray-400 truncate">{{ authStore.profile?.email }}</p>
        </div>
        <button
          class="w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-white/5 transition-colors"
          @click="router.push('/settings'); userMenuOpen = false"
        >
          Settings
        </button>
        <button
          class="w-full text-left px-4 py-2 text-sm text-red-600 dark:text-red-400 hover:bg-gray-50 dark:hover:bg-white/5 transition-colors"
          @click="handleLogout"
        >
          Sign out
        </button>
      </div>
    </div>
  </header>

  <!-- Click outside overlay -->
  <div
    v-if="userMenuOpen || notifOpen"
    class="fixed inset-0 z-40"
    @click="userMenuOpen = false; notifOpen = false"
  />
</template>
