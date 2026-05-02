<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useMessageStore } from '@/stores/messages'
import { useWorkspaceStore } from '@/stores/workspace'
import { usePresenceStore } from '@/stores/presence'
import MessageList from '@/components/chat/MessageList.vue'
import MessageInput from '@/components/chat/MessageInput.vue'
import Avatar from '@/components/shared/Avatar.vue'
import type { Channel } from '@/types'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const messageStore = useMessageStore()
const workspaceStore = useWorkspaceStore()
const presenceStore = usePresenceStore()

const showNewDM = ref(false)
const newDMUserId = ref('')

const dmChannels = computed(() =>
  messageStore.channels.filter((c) => c.type === 'dm')
)

const targetUserId = computed(() => route.params.userId as string)

const currentDMChannel = computed(() => messageStore.currentChannel)

watch(
  targetUserId,
  async (uid) => {
    if (!uid || !workspaceStore.currentWorkspaceId) return
    const channel = await messageStore.createDM(workspaceStore.currentWorkspaceId, uid)
    await messageStore.selectChannel(channel)
  },
  { immediate: true }
)

async function startNewDM() {
  if (!newDMUserId.value.trim() || !workspaceStore.currentWorkspaceId) return
  const channel = await messageStore.createDM(
    workspaceStore.currentWorkspaceId,
    newDMUserId.value.trim()
  )
  await messageStore.selectChannel(channel)
  showNewDM.value = false
  newDMUserId.value = ''
  router.push(`/dm/${newDMUserId.value}`)
}

function getDMName(channel: Channel): string {
  return channel.name || 'Direct Message'
}

function getDMUserId(channel: Channel): string {
  return channel.member_ids.find((id) => id !== authStore.profile?.id) ?? ''
}

onMounted(async () => {
  if (!authStore.isAuthenticated) {
    router.replace('/login')
    return
  }
  await workspaceStore.fetchWorkspaces()
  if (workspaceStore.currentWorkspaceId) {
    await messageStore.fetchChannels(workspaceStore.currentWorkspaceId)
    presenceStore.subscribeToPresence(workspaceStore.currentWorkspaceId)
  }
})
</script>

<template>
  <div class="flex h-full overflow-hidden">
    <!-- DM List sidebar -->
    <div class="w-64 border-r border-gray-200 dark:border-gray-700 bg-white dark:bg-surface-dark-elevated flex flex-col">
      <div class="p-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
        <h2 class="font-semibold text-gray-900 dark:text-white text-sm">Direct Messages</h2>
        <button
          class="text-gray-400 hover:text-brand-500 text-lg leading-none"
          @click="showNewDM = true"
        >
          +
        </button>
      </div>

      <div class="flex-1 overflow-y-auto p-2">
        <button
          v-for="channel in dmChannels"
          :key="channel.id"
          class="w-full flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-gray-100 dark:hover:bg-white/5 transition-colors text-left"
          :class="{
            'bg-brand-50 dark:bg-brand-900/20': currentDMChannel?.id === channel.id,
          }"
          @click="router.push(`/dm/${getDMUserId(channel)}`)"
        >
          <div class="relative">
            <Avatar
              :name="getDMName(channel)"
              size="sm"
              :show-presence="true"
              :presence-status="presenceStore.getStatus(getDMUserId(channel))"
            />
          </div>
          <span class="text-sm text-gray-700 dark:text-gray-300 truncate">
            {{ getDMName(channel) }}
          </span>
          <span
            v-if="channel.unread_count"
            class="ml-auto text-xs bg-brand-500 text-white rounded-full px-1.5 py-0.5"
          >
            {{ channel.unread_count }}
          </span>
        </button>
      </div>

      <!-- New DM form -->
      <div v-if="showNewDM" class="p-4 border-t border-gray-200 dark:border-gray-700">
        <p class="text-xs text-gray-500 mb-2">User ID to message</p>
        <div class="flex gap-2">
          <input
            v-model="newDMUserId"
            type="text"
            placeholder="user-id"
            class="flex-1 text-sm border border-gray-300 dark:border-gray-600 rounded-lg px-2 py-1.5 bg-white dark:bg-surface-dark text-gray-800 dark:text-gray-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
            @keydown.enter="startNewDM"
          />
          <button
            class="text-sm px-3 py-1.5 bg-brand-500 text-white rounded-lg hover:bg-brand-600"
            @click="startNewDM"
          >
            Start
          </button>
        </div>
        <button
          class="mt-1 text-xs text-gray-400 hover:text-gray-600"
          @click="showNewDM = false"
        >
          Cancel
        </button>
      </div>
    </div>

    <!-- DM chat area -->
    <div class="flex flex-col flex-1 min-w-0">
      <div class="flex items-center gap-3 px-6 py-4 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-surface-dark-elevated">
        <Avatar
          :name="currentDMChannel?.name ?? 'User'"
          size="sm"
          :show-presence="true"
          :presence-status="presenceStore.getStatus(targetUserId)"
        />
        <div>
          <h1 class="font-semibold text-gray-900 dark:text-white text-sm">
            {{ currentDMChannel?.name ?? 'Direct Message' }}
          </h1>
          <p class="text-xs text-gray-400 capitalize">
            {{ presenceStore.getStatus(targetUserId) }}
          </p>
        </div>
      </div>

      <MessageList class="flex-1 overflow-y-auto" />

      <div class="px-4 py-3 border-t border-gray-200 dark:border-gray-700">
        <MessageInput
          :channel-id="currentDMChannel?.id ?? ''"
          :placeholder="`Message ${currentDMChannel?.name ?? ''}`"
        />
      </div>
    </div>
  </div>
</template>
