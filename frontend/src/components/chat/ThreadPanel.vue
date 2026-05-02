<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import { useMessageStore } from '@/stores/messages'
import MessageInput from './MessageInput.vue'
import Avatar from '@/components/shared/Avatar.vue'
import { format } from 'date-fns'
import type { Message } from '@/types'

const props = defineProps<{
  parentMessage: Message
}>()

const emit = defineEmits<{
  close: []
}>()

const messageStore = useMessageStore()
const replies = ref<Message[]>([])
const loading = ref(true)

function renderMarkdown(body: string): string {
  const raw = marked.parse(body, { async: false }) as string
  return DOMPurify.sanitize(raw)
}

function formatTime(dateStr: string) {
  return format(new Date(dateStr), 'MMM d, HH:mm')
}

async function sendReply(body: string) {
  if (!messageStore.currentChannel) return
  const { data } = await import('@/lib/api').then((m) =>
    m.default.post(`/api/v1/messages/${messageStore.currentChannel!.id}`, {
      body,
      thread_id: props.parentMessage.id,
    })
  )
  replies.value.push(data)
}

onMounted(async () => {
  if (!messageStore.currentChannel) return
  try {
    const { default: api } = await import('@/lib/api')
    const { data } = await api.get(
      `/api/v1/messages/${messageStore.currentChannel.id}/${props.parentMessage.id}/thread`
    )
    replies.value = data
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="flex flex-col h-full bg-white dark:bg-surface-dark-elevated">
    <!-- Header -->
    <div class="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-gray-700">
      <h2 class="font-semibold text-gray-900 dark:text-white text-sm">Thread</h2>
      <button
        class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition-colors"
        @click="emit('close')"
      >
        ✕
      </button>
    </div>

    <!-- Parent message -->
    <div class="px-4 py-3 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50">
      <div class="flex gap-3">
        <Avatar
          :src="parentMessage.author?.avatar_url"
          :name="parentMessage.author?.display_name ?? 'User'"
          size="sm"
        />
        <div>
          <div class="flex items-baseline gap-2 mb-1">
            <span class="text-sm font-semibold text-gray-900 dark:text-white">
              {{ parentMessage.author?.display_name ?? 'Unknown' }}
            </span>
            <span class="text-xs text-gray-400">{{ formatTime(parentMessage.created_at) }}</span>
          </div>
          <!-- eslint-disable vue/no-v-html -->
          <div
            class="prose prose-sm dark:prose-invert max-w-none text-gray-700 dark:text-gray-300"
            v-html="renderMarkdown(parentMessage.body)"
          />
        </div>
      </div>
    </div>

    <!-- Replies -->
    <div class="flex-1 overflow-y-auto px-4 py-2">
      <div v-if="loading" class="text-center py-4 text-gray-400 text-sm">Loading…</div>
      <div v-else-if="replies.length === 0" class="text-center py-4 text-gray-400 text-sm">
        No replies yet. Start the thread!
      </div>
      <div
        v-for="reply in replies"
        :key="reply.id"
        class="flex gap-2 py-2"
      >
        <Avatar
          :src="reply.author?.avatar_url"
          :name="reply.author?.display_name ?? 'User'"
          size="xs"
          class="flex-shrink-0 mt-1"
        />
        <div>
          <div class="flex items-baseline gap-2 mb-0.5">
            <span class="text-xs font-semibold text-gray-800 dark:text-gray-200">
              {{ reply.author?.display_name ?? 'Unknown' }}
            </span>
            <span class="text-xs text-gray-400">{{ formatTime(reply.created_at) }}</span>
          </div>
          <div
            class="prose prose-sm dark:prose-invert max-w-none text-sm text-gray-700 dark:text-gray-300"
            v-html="renderMarkdown(reply.body)"
          />
        </div>
      </div>
    </div>

    <!-- Reply input -->
    <div class="px-4 py-3 border-t border-gray-200 dark:border-gray-700">
      <MessageInput
        :channel-id="messageStore.currentChannel?.id ?? ''"
        placeholder="Reply in thread…"
      />
    </div>
  </div>
</template>
