<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useWorkspaceStore } from '@/stores/workspace'
import api from '@/lib/api'
import type { DigestFreq } from '@/types'

const router = useRouter()
const authStore = useAuthStore()
const workspaceStore = useWorkspaceStore()

type Tab = 'profile' | 'workspace' | 'notifications' | 'integrations'
const activeTab = ref<Tab>('profile')

const profileForm = reactive({
  display_name: '',
  avatar_url: '',
})
const profileSaving = ref(false)
const profileSaved = ref(false)

const workspaceForm = reactive({
  name: '',
  slug: '',
  github_org: '',
})
const workspaceSaving = ref(false)

const notifForm = reactive({
  email_digest: 'daily' as DigestFreq,
  push_enabled: true,
  mention_only: false,
})
const notifSaving = ref(false)

const githubConnected = ref(false)

const tabs: { key: Tab; label: string }[] = [
  { key: 'profile', label: 'Profile' },
  { key: 'workspace', label: 'Workspace' },
  { key: 'notifications', label: 'Notifications' },
  { key: 'integrations', label: 'Integrations' },
]

async function saveProfile() {
  profileSaving.value = true
  try {
    await api.patch('/api/v1/users/me', {
      display_name: profileForm.display_name,
    })
    if (authStore.profile) {
      authStore.profile.display_name = profileForm.display_name
    }
    profileSaved.value = true
    setTimeout(() => (profileSaved.value = false), 2000)
  } finally {
    profileSaving.value = false
  }
}

async function saveWorkspace() {
  if (!workspaceStore.currentWorkspaceId) return
  workspaceSaving.value = true
  try {
    await api.patch(`/api/v1/workspaces/${workspaceStore.currentWorkspaceId}`, {
      name: workspaceForm.name,
      settings: { github_org: workspaceForm.github_org || null },
    })
    await workspaceStore.fetchWorkspaces()
  } finally {
    workspaceSaving.value = false
  }
}

async function saveNotifications() {
  notifSaving.value = true
  try {
    await api.patch('/api/v1/users/me', {
      notification_prefs: {
        email_digest: notifForm.email_digest,
        push_enabled: notifForm.push_enabled,
        mention_only: notifForm.mention_only,
      },
    })
  } finally {
    notifSaving.value = false
  }
}

onMounted(async () => {
  if (!authStore.isAuthenticated) {
    router.replace('/login')
    return
  }
  // Prefill forms
  if (authStore.profile) {
    profileForm.display_name = authStore.profile.display_name
    profileForm.avatar_url = authStore.profile.avatar_url ?? ''
    const prefs = authStore.profile.notification_prefs
    if (prefs) {
      notifForm.email_digest = prefs.email_digest
      notifForm.push_enabled = prefs.push_enabled
      notifForm.mention_only = prefs.mention_only
    }
  }
  await workspaceStore.fetchWorkspaces()
  const ws = workspaceStore.currentWorkspace
  if (ws) {
    workspaceForm.name = ws.name
    workspaceForm.slug = ws.slug
    workspaceForm.github_org = ws.settings.github_org ?? ''
  }
})
</script>

<template>
  <div class="flex-1 overflow-y-auto p-6 bg-gray-50 dark:bg-surface-dark">
    <div class="max-w-3xl mx-auto">
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white mb-6">Settings</h1>

      <!-- Tab nav -->
      <div class="flex gap-1 bg-white dark:bg-surface-dark-elevated rounded-xl p-1 shadow-sm mb-6">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          class="flex-1 py-2 text-sm font-medium rounded-lg transition-colors"
          :class="
            activeTab === tab.key
              ? 'bg-brand-500 text-white shadow'
              : 'text-gray-500 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200'
          "
          @click="activeTab = tab.key"
        >
          {{ tab.label }}
        </button>
      </div>

      <!-- Profile Tab -->
      <div v-if="activeTab === 'profile'" class="bg-white dark:bg-surface-dark-elevated rounded-xl shadow-sm p-6 space-y-5">
        <!-- Avatar preview -->
        <div class="flex items-center gap-4">
          <div class="w-20 h-20 rounded-full overflow-hidden bg-brand-100 flex items-center justify-center">
            <img
              v-if="profileForm.avatar_url"
              :src="profileForm.avatar_url"
              alt="Avatar"
              class="w-full h-full object-cover"
            />
            <span v-else class="text-2xl font-bold text-brand-500">
              {{ (profileForm.display_name || 'U')[0].toUpperCase() }}
            </span>
          </div>
          <div>
            <p class="text-sm font-medium text-gray-700 dark:text-gray-300">Profile photo</p>
            <p class="text-xs text-gray-400 mt-0.5">
              {{ authStore.profile?.email }}
            </p>
          </div>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Display Name
          </label>
          <input
            v-model="profileForm.display_name"
            type="text"
            class="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-surface-dark text-gray-800 dark:text-gray-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
          />
        </div>

        <button
          :disabled="profileSaving"
          class="px-4 py-2 bg-brand-500 text-white text-sm font-medium rounded-lg hover:bg-brand-600 disabled:opacity-50 transition-colors"
          @click="saveProfile"
        >
          {{ profileSaved ? '✓ Saved' : profileSaving ? 'Saving…' : 'Save Changes' }}
        </button>
      </div>

      <!-- Workspace Tab -->
      <div v-else-if="activeTab === 'workspace'" class="bg-white dark:bg-surface-dark-elevated rounded-xl shadow-sm p-6 space-y-5">
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Workspace Name
          </label>
          <input
            v-model="workspaceForm.name"
            type="text"
            class="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-surface-dark text-gray-800 dark:text-gray-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Slug
          </label>
          <input
            :value="workspaceForm.slug"
            type="text"
            disabled
            class="w-full border border-gray-200 dark:border-gray-700 rounded-lg px-3 py-2 text-sm bg-gray-50 dark:bg-gray-800 text-gray-400 cursor-not-allowed"
          />
          <p class="text-xs text-gray-400 mt-1">Slugs cannot be changed after creation.</p>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            GitHub Organization
          </label>
          <input
            v-model="workspaceForm.github_org"
            type="text"
            placeholder="my-org"
            class="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-surface-dark text-gray-800 dark:text-gray-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
          />
        </div>

        <button
          :disabled="workspaceSaving"
          class="px-4 py-2 bg-brand-500 text-white text-sm font-medium rounded-lg hover:bg-brand-600 disabled:opacity-50 transition-colors"
          @click="saveWorkspace"
        >
          {{ workspaceSaving ? 'Saving…' : 'Save Workspace' }}
        </button>
      </div>

      <!-- Notifications Tab -->
      <div v-else-if="activeTab === 'notifications'" class="bg-white dark:bg-surface-dark-elevated rounded-xl shadow-sm p-6 space-y-6">
        <div>
          <p class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">Email Digest</p>
          <div class="flex gap-3">
            <label
              v-for="opt in ['none', 'daily', 'weekly']"
              :key="opt"
              class="flex items-center gap-2 cursor-pointer"
            >
              <input
                v-model="notifForm.email_digest"
                type="radio"
                :value="opt"
                class="accent-brand-500"
              />
              <span class="text-sm text-gray-600 dark:text-gray-400 capitalize">{{ opt }}</span>
            </label>
          </div>
        </div>

        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm font-medium text-gray-700 dark:text-gray-300">Push Notifications</p>
            <p class="text-xs text-gray-400">Receive notifications in your browser</p>
          </div>
          <button
            class="relative w-11 h-6 rounded-full transition-colors"
            :class="notifForm.push_enabled ? 'bg-brand-500' : 'bg-gray-300 dark:bg-gray-600'"
            @click="notifForm.push_enabled = !notifForm.push_enabled"
          >
            <span
              class="absolute top-1 w-4 h-4 bg-white rounded-full shadow transition-transform"
              :class="notifForm.push_enabled ? 'translate-x-6' : 'translate-x-1'"
            />
          </button>
        </div>

        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm font-medium text-gray-700 dark:text-gray-300">Mentions Only</p>
            <p class="text-xs text-gray-400">Only notify on @mentions</p>
          </div>
          <button
            class="relative w-11 h-6 rounded-full transition-colors"
            :class="notifForm.mention_only ? 'bg-brand-500' : 'bg-gray-300 dark:bg-gray-600'"
            @click="notifForm.mention_only = !notifForm.mention_only"
          >
            <span
              class="absolute top-1 w-4 h-4 bg-white rounded-full shadow transition-transform"
              :class="notifForm.mention_only ? 'translate-x-6' : 'translate-x-1'"
            />
          </button>
        </div>

        <button
          :disabled="notifSaving"
          class="px-4 py-2 bg-brand-500 text-white text-sm font-medium rounded-lg hover:bg-brand-600 disabled:opacity-50 transition-colors"
          @click="saveNotifications"
        >
          {{ notifSaving ? 'Saving…' : 'Save Preferences' }}
        </button>
      </div>

      <!-- Integrations Tab -->
      <div v-else-if="activeTab === 'integrations'" class="bg-white dark:bg-surface-dark-elevated rounded-xl shadow-sm p-6">
        <div class="flex items-center justify-between p-4 border border-gray-200 dark:border-gray-700 rounded-xl">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 bg-gray-900 rounded-xl flex items-center justify-center">
              <svg class="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z" />
              </svg>
            </div>
            <div>
              <p class="text-sm font-medium text-gray-900 dark:text-white">GitHub</p>
              <p class="text-xs text-gray-400">
                {{ githubConnected ? 'Connected' : 'Not connected' }}
              </p>
            </div>
          </div>
          <button
            class="px-3 py-1.5 text-sm font-medium rounded-lg border transition-colors"
            :class="
              githubConnected
                ? 'border-red-300 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20'
                : 'border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-white/5'
            "
            @click="githubConnected = !githubConnected"
          >
            {{ githubConnected ? 'Disconnect' : 'Connect' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
