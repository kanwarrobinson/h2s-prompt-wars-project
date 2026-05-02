<script setup lang="ts">
import { ref, computed, nextTick, watch } from 'vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import { format, isToday } from 'date-fns'
import { useMessageStore } from '@/stores/messages'
import { useAuthStore } from '@/stores/auth'
import Avatar from '@/components/shared/Avatar.vue'
import type { Message } from '@/types'

const props = defineProps<{
  typingUsers?: string[]
}>()

const emit = defineEmits<{
  openThread: [message: Message]
}>()

const messageStore = useMessageStore()
const authStore = useAuthStore()

const listRef = ref<HTMLElement | null>(null)
const hoveredId = ref<string | null>(null)

const messages = computed(() => messageStore.sortedMessages)
const hasMore = computed(() => messageStore.hasMore)
const cursor = computed(() => messageStore.cursor)

function renderMarkdown(body: string): string {
  const raw = marked.parse(body, { async: false }) as string
  return DOMPurify.sanitize(raw)
}

function formatTime(dateStr: string) {
  const d = new Date(dateStr)
  if (isToday(d)) return format(d, 'HH:mm')
  return format(d, 'MMM d, HH:mm')
}

function isSameAuthorGroup(idx: number): boolean {
  if (idx === 0) return false
  const prev = messages.value[idx - 1]
  const curr = messages.value[idx]
  if (prev.author_id !== curr.author_id) return false
  const diff =
    new Date(curr.created_at).getTime() - new Date(prev.created_at).getTime()
  return diff < 5 * 60 * 1000 // 5 minutes
}

async function loadOlder() {
  if (!messageStore.currentChannel || !cursor.value) return
  await messageStore.fetchMessages(messageStore.currentChannel.id, cursor.value)
}

async function addReaction(messageId: string, emoji: string) {
  if (!messageStore.currentChannel) return
  await messageStore.addReaction(messageStore.currentChannel.id, messageId, emoji)
}

function scrollToBottom() {
  nextTick(() => {
    if (listRef.value) {
      listRef.value.scrollTop = listRef.value.scrollHeight
    }
  })
}

watch(messages, scrollToBottom)
</script>

<template>
  <div ref="listRef" class="flex flex-col px-4 py-2 space-y-1">
    <!-- Load older button -->
    <div class="flex justify-center py-2">
      <button
        v-if="hasMore"
        class="text-xs text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors px-4 py-1.5 rounded-full bg-gray-100 dark:bg-gray-800"
        :disabled="messageStore.loading"
        @click="loadOlder"
      >
        {{ messageStore.loading ? 'Loading…' : 'Load older messages' }}
      </button>
    </div>

    <!-- Messages -->
    <div
      v-for="(message, idx) in messages"
      :key="message.id"
      class="group relative"
      @mouseenter="hoveredId = message.id"
      @mouseleave="hoveredId = null"
    >
      <div class="flex gap-3" :class="isSameAuthorGroup(idx) ? 'pl-11' : ''">
        <!-- Avatar (only on first message of a group) -->
        <Avatar
          v-if="!isSameAuthorGroup(idx)"
          :src="message.author?.avatar_url"
          :name="message.author?.display_name ?? 'User'"
          size="sm"
          class="flex-shrink-0 mt-1"
        />

        <div class="flex-1 min-w-0">
          <!-- Author + timestamp (first in group) -->
          <div v-if="!isSameAuthorGroup(idx)" class="flex items-baseline gap-2 mb-0.5">
            <span class="text-sm font-semibold text-gray-900 dark:text-white">
              {{ message.author?.display_name ?? 'Unknown' }}
            </span>
            <span class="text-xs text-gray-400">{{ formatTime(message.created_at) }}</span>
            <span v-if="message.edited" class="text-xs text-gray-400 italic">(edited)</span>
          </div>

          <!-- Message body (rendered markdown) -->
          <!-- eslint-disable vue/no-v-html -->
          <div
            class="prose prose-sm dark:prose-invert max-w-none text-gray-700 dark:text-gray-300"
            v-html="renderMarkdown(message.body)"
          />

          <!-- Reactions -->
          <div v-if="message.reactions.length" class="flex flex-wrap gap-1 mt-1">
            <button
              v-for="reaction in message.reactions"
              :key="reaction.emoji"
              class="flex items-center gap-1 text-xs px-1.5 py-0.5 rounded-full border border-gray-200 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              :class="
                reaction.user_ids.includes(authStore.profile?.id ?? '')
                  ? 'bg-brand-50 border-brand-300 dark:bg-brand-900/30 dark:border-brand-700'
                  : ''
              "
              @click="addReaction(message.id, reaction.emoji)"
            >
              {{ reaction.emoji }}
              <span class="text-gray-600 dark:text-gray-400">{{ reaction.user_ids.length }}</span>
            </button>
          </div>
        </div>

        <!-- Hover actions -->
        <div
          v-if="hoveredId === message.id"
          class="absolute right-2 top-0 flex items-center gap-1 bg-white dark:bg-surface-dark-elevated border border-gray-200 dark:border-gray-700 rounded-lg shadow-sm px-1 py-0.5"
        >
          <button
            class="p-1 text-sm hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-colors"
            title="Add reaction"
            @click="addReaction(message.id, '👍')"
          >
            😊
          </button>
          <button
            class="p-1 text-sm hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-colors"
            title="Reply in thread"
            @click="emit('openThread', message)"
          >
            💬
          </button>
        </div>
      </div>
    </div>

    <!-- Typing indicators -->
    <div v-if="typingUsers && typingUsers.length" class="flex items-center gap-2 px-2 py-1">
      <div class="flex gap-0.5">
        <span
          v-for="i in 3"
          :key="i"
          class="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce"
          :style="{ animationDelay: `${(i - 1) * 150}ms` }"
        />
      </div>
      <span class="text-xs text-gray-400">
        {{ typingUsers.join(', ') }} {{ typingUsers.length === 1 ? 'is' : 'are' }} typing…
      </span>
    </div>
  </div>
</template>
