<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useWorkspaceStore } from '@/stores/workspace'
import { useMessageStore } from '@/stores/messages'
import { usePresenceStore } from '@/stores/presence'
import Avatar from './Avatar.vue'
import PresenceDot from './PresenceDot.vue'
import type { PresenceStatus } from '@/types'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const workspaceStore = useWorkspaceStore()
const messageStore = useMessageStore()
const presenceStore = usePresenceStore()

const channelsOpen = ref(true)
const dmsOpen = ref(true)
const workspaceSwitcherOpen = ref(false)
const myPresence = ref<PresenceStatus>('online')
const mobileOpen = ref(false)

const publicChannels = computed(() =>
  messageStore.channels.filter((c) => c.type !== 'dm')
)
const dmChannels = computed(() =>
  messageStore.channels.filter((c) => c.type === 'dm')
)

const navLinks = [
  { path: '/dashboard', label: 'Dashboard', icon: '🏠' },
  { path: '/board', label: 'Sprint Board', icon: '📋' },
  { path: '/roadmap', label: 'Roadmap', icon: '🗺️' },
]

function isActive(path: string) {
  return route.path === path
}

function dmPartnerName(channelName: string) {
  return channelName || 'Direct Message'
}

function dmPartnerId(memberIds: string[]) {
  return memberIds.find((id) => id !== authStore.profile?.id) ?? ''
}

async function switchWorkspace(id: string) {
  await workspaceStore.selectWorkspace(id)
  workspaceSwitcherOpen.value = false
}

async function updatePresence(status: PresenceStatus) {
  myPresence.value = status
  if (workspaceStore.currentWorkspaceId && authStore.profile?.id) {
    await presenceStore.updateMyPresence(
      workspaceStore.currentWorkspaceId,
      authStore.profile.id,
      status
    )
  }
}
</script>

<template>
  <!-- Mobile overlay -->
  <div
    v-if="mobileOpen"
    class="fixed inset-0 bg-black/40 z-20 md:hidden"
    @click="mobileOpen = false"
  />

  <!-- Sidebar -->
  <aside
    class="fixed inset-y-0 left-0 z-30 w-64 bg-gray-900 text-gray-100 flex flex-col transition-transform duration-200 md:relative md:translate-x-0"
    :class="mobileOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'"
  >
    <!-- Logo + Workspace Switcher -->
    <div class="p-4 border-b border-gray-700">
      <button
        class="w-full flex items-center gap-2 hover:bg-gray-800 rounded-lg p-2 transition-colors"
        @click="workspaceSwitcherOpen = !workspaceSwitcherOpen"
      >
        <div class="w-7 h-7 bg-brand-500 rounded-lg flex items-center justify-center text-white font-bold text-sm flex-shrink-0">
          D
        </div>
        <span class="font-semibold truncate flex-1 text-left text-sm">
          {{ workspaceStore.currentWorkspace?.name ?? 'DevCollab' }}
        </span>
        <span class="text-gray-400 text-xs">▾</span>
      </button>

      <!-- Workspace switcher dropdown -->
      <div
        v-if="workspaceSwitcherOpen"
        class="mt-1 bg-gray-800 rounded-lg overflow-hidden shadow-lg"
      >
        <button
          v-for="ws in workspaceStore.workspaces"
          :key="ws.id"
          class="w-full px-3 py-2 text-left text-sm hover:bg-gray-700 transition-colors"
          :class="ws.id === workspaceStore.currentWorkspaceId ? 'text-brand-400' : 'text-gray-300'"
          @click="switchWorkspace(ws.id)"
        >
          {{ ws.name }}
        </button>
        <button
          class="w-full px-3 py-2 text-left text-xs text-gray-500 hover:text-gray-300 border-t border-gray-700"
          @click="router.push('/settings'); workspaceSwitcherOpen = false"
        >
          + New Workspace
        </button>
      </div>
    </div>

    <!-- Navigation -->
    <nav class="px-3 py-3 space-y-0.5">
      <button
        v-for="link in navLinks"
        :key="link.path"
        class="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors"
        :class="
          isActive(link.path)
            ? 'bg-gray-700 text-white'
            : 'text-gray-400 hover:bg-gray-800 hover:text-white'
        "
        @click="router.push(link.path)"
      >
        <span>{{ link.icon }}</span>
        <span>{{ link.label }}</span>
      </button>
    </nav>

    <!-- Channels -->
    <div class="px-3 py-2 flex-1 overflow-y-auto">
      <div>
        <button
          class="w-full flex items-center justify-between px-3 py-1.5 text-xs font-semibold text-gray-400 uppercase tracking-wide hover:text-gray-200 transition-colors"
          @click="channelsOpen = !channelsOpen"
        >
          <span>Channels</span>
          <span>{{ channelsOpen ? '▾' : '▸' }}</span>
        </button>
        <div v-if="channelsOpen" class="space-y-0.5 mt-1">
          <button
            v-for="channel in publicChannels"
            :key="channel.id"
            class="w-full flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm transition-colors"
            :class="
              route.params.channelId === channel.id
                ? 'bg-gray-700 text-white'
                : 'text-gray-400 hover:bg-gray-800 hover:text-white'
            "
            @click="router.push(`/channels/${channel.id}`)"
          >
            <span class="text-gray-500">#</span>
            <span class="truncate flex-1 text-left">{{ channel.name }}</span>
            <span
              v-if="channel.unread_count"
              class="bg-brand-500 text-white text-xs rounded-full px-1.5"
            >
              {{ channel.unread_count }}
            </span>
          </button>
        </div>
      </div>

      <!-- DMs -->
      <div class="mt-4">
        <button
          class="w-full flex items-center justify-between px-3 py-1.5 text-xs font-semibold text-gray-400 uppercase tracking-wide hover:text-gray-200 transition-colors"
          @click="dmsOpen = !dmsOpen"
        >
          <span>Direct Messages</span>
          <span>{{ dmsOpen ? '▾' : '▸' }}</span>
        </button>
        <div v-if="dmsOpen" class="space-y-0.5 mt-1">
          <button
            v-for="channel in dmChannels"
            :key="channel.id"
            class="w-full flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm transition-colors"
            :class="
              route.path.includes(dmPartnerId(channel.member_ids))
                ? 'bg-gray-700 text-white'
                : 'text-gray-400 hover:bg-gray-800 hover:text-white'
            "
            @click="router.push(`/dm/${dmPartnerId(channel.member_ids)}`)"
          >
            <div class="relative flex-shrink-0">
              <Avatar
                :name="dmPartnerName(channel.name)"
                size="xs"
                :show-presence="true"
                :presence-status="presenceStore.getStatus(dmPartnerId(channel.member_ids))"
              />
            </div>
            <span class="truncate flex-1 text-left">{{ dmPartnerName(channel.name) }}</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Bottom user section -->
    <div class="p-3 border-t border-gray-700">
      <div class="flex items-center gap-2 p-2 rounded-lg hover:bg-gray-800 transition-colors cursor-pointer">
        <Avatar
          :src="authStore.avatarUrl"
          :name="authStore.displayName || 'User'"
          size="sm"
          :show-presence="true"
          :presence-status="myPresence"
        />
        <div class="flex-1 min-w-0">
          <p class="text-sm font-medium text-white truncate">{{ authStore.displayName }}</p>
        </div>
        <!-- Presence selector -->
        <select
          v-model="myPresence"
          class="text-xs bg-transparent text-gray-400 border-none outline-none cursor-pointer"
          @change="updatePresence(myPresence)"
        >
          <option value="online">🟢</option>
          <option value="away">🟡</option>
          <option value="offline">⚫</option>
        </select>
      </div>
      <button
        class="mt-1 w-full text-xs text-gray-500 hover:text-gray-300 transition-colors text-left px-2 py-1"
        @click="authStore.logout().then(() => router.push('/login'))"
      >
        Sign out
      </button>
    </div>
  </aside>
</template>
