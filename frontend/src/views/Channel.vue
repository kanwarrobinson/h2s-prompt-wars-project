<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useMessageStore } from '@/stores/messages'
import { useWorkspaceStore } from '@/stores/workspace'
import { useWebSocket } from '@/composables/useWebSocket'
import MessageList from '@/components/chat/MessageList.vue'
import MessageInput from '@/components/chat/MessageInput.vue'
import ThreadPanel from '@/components/chat/ThreadPanel.vue'
import type { Message } from '@/types'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const messageStore = useMessageStore()
const workspaceStore = useWorkspaceStore()

const activeThread = ref<Message | null>(null)
const typingUsers = ref<string[]>([])

const channelId = computed(() => route.params.channelId as string)
const currentChannel = computed(() => messageStore.currentChannel)

let ws: ReturnType<typeof useWebSocket> | null = null

watch(
  channelId,
  async (id) => {
    if (!id) return
    const channel = messageStore.channelById(id)
    if (channel) {
      await messageStore.selectChannel(channel)
    }
    activeThread.value = null
  },
  { immediate: true }
)

watch(
  () => ws?.messages.value,
  (msgs) => {
    if (!msgs) return
    const latest = msgs[msgs.length - 1] as Record<string, unknown>
    if (!latest) return
    if (latest.type === 'message') {
      messageStore.appendLiveMessage(latest.data as Message)
    }
    if (latest.type === 'typing') {
      const user = latest.user_name as string
      if (!typingUsers.value.includes(user)) {
        typingUsers.value.push(user)
        setTimeout(() => {
          typingUsers.value = typingUsers.value.filter((u) => u !== user)
        }, 3000)
      }
    }
  },
  { deep: true }
)

async function sendTyping() {
  ws?.sendTyping(channelId.value)
}

onMounted(async () => {
  if (!authStore.isAuthenticated) {
    router.replace('/login')
    return
  }
  await workspaceStore.fetchWorkspaces()
  if (workspaceStore.currentWorkspaceId) {
    await messageStore.fetchChannels(workspaceStore.currentWorkspaceId)
    ws = useWebSocket(workspaceStore.currentWorkspaceId)
  }
})

onUnmounted(() => {
  ws?.disconnect()
})
</script>

<template>
  <div class="flex h-full overflow-hidden">
    <!-- Main channel area -->
    <div class="flex flex-col flex-1 min-w-0">
      <!-- Channel header -->
      <div class="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-surface-dark-elevated">
        <div>
          <h1 class="font-semibold text-gray-900 dark:text-white">
            # {{ currentChannel?.name ?? channelId }}
          </h1>
          <p v-if="currentChannel?.topic" class="text-xs text-gray-400 mt-0.5 truncate max-w-md">
            {{ currentChannel.topic }}
          </p>
        </div>
        <div class="text-xs text-gray-400">
          {{ currentChannel?.member_ids.length ?? 0 }} members
        </div>
      </div>

      <!-- Message list -->
      <MessageList
        class="flex-1 overflow-y-auto"
        :typing-users="typingUsers"
        @open-thread="(msg) => (activeThread = msg)"
      />

      <!-- Message input -->
      <div class="px-4 py-3 border-t border-gray-200 dark:border-gray-700">
        <MessageInput
          :channel-id="channelId"
          :placeholder="`Message #${currentChannel?.name ?? channelId}`"
          @typing="sendTyping"
        />
      </div>
    </div>

    <!-- Thread panel -->
    <Transition name="slide">
      <ThreadPanel
        v-if="activeThread"
        :parent-message="activeThread"
        class="w-80 border-l border-gray-200 dark:border-gray-700"
        @close="activeThread = null"
      />
    </Transition>
  </div>
</template>

<style scoped>
.slide-enter-active,
.slide-leave-active {
  transition: transform 0.2s ease, opacity 0.2s ease;
}
.slide-enter-from,
.slide-leave-to {
  transform: translateX(100%);
  opacity: 0;
}
</style>
