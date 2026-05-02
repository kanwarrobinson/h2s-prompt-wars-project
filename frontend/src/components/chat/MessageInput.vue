<script setup lang="ts">
import { ref, computed } from 'vue'
import { useMessageStore } from '@/stores/messages'

const props = defineProps<{
  channelId: string
  placeholder?: string
}>()

const emit = defineEmits<{
  typing: []
}>()

const messageStore = useMessageStore()

const body = ref('')
const sending = ref(false)
const showEmojiPicker = ref(false)
const MAX_CHARS = 2000

const charCount = computed(() => body.value.length)
const overLimit = computed(() => charCount.value > MAX_CHARS)

const emojis = ['😀', '😂', '❤️', '👍', '🎉', '🔥', '😢', '🤔', '👋', '✅', '❌', '🚀']

let typingTimer: ReturnType<typeof setTimeout> | null = null

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    send()
    return
  }
  // Emit typing with debounce
  if (typingTimer) clearTimeout(typingTimer)
  emit('typing')
  typingTimer = setTimeout(() => {
    typingTimer = null
  }, 1000)
}

async function send() {
  const text = body.value.trim()
  if (!text || sending.value || overLimit.value) return
  sending.value = true
  try {
    await messageStore.sendMessage(props.channelId, text)
    body.value = ''
  } finally {
    sending.value = false
  }
}

function insertEmoji(emoji: string) {
  body.value += emoji
  showEmojiPicker.value = false
}

function autoResize(e: Event) {
  const el = e.target as HTMLTextAreaElement
  el.style.height = 'auto'
  el.style.height = `${Math.min(el.scrollHeight, 200)}px`
}
</script>

<template>
  <div class="relative">
    <div
      class="flex items-end gap-2 bg-white dark:bg-surface-dark-elevated border border-gray-200 dark:border-gray-600 rounded-xl px-3 py-2 focus-within:ring-2 focus-within:ring-brand-500 focus-within:border-transparent"
    >
      <!-- Emoji button -->
      <div class="relative">
        <button
          class="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
          @click="showEmojiPicker = !showEmojiPicker"
        >
          😊
        </button>
        <!-- Emoji picker -->
        <div
          v-if="showEmojiPicker"
          class="absolute bottom-full mb-2 left-0 bg-white dark:bg-surface-dark-elevated border border-gray-200 dark:border-gray-700 rounded-xl shadow-xl p-2 grid grid-cols-6 gap-1 z-50"
        >
          <button
            v-for="emoji in emojis"
            :key="emoji"
            class="p-1 text-lg hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
            @click="insertEmoji(emoji)"
          >
            {{ emoji }}
          </button>
        </div>
      </div>

      <!-- Textarea -->
      <textarea
        v-model="body"
        rows="1"
        :placeholder="placeholder ?? 'Type a message…'"
        class="flex-1 resize-none bg-transparent text-sm text-gray-800 dark:text-gray-200 placeholder-gray-400 focus:outline-none min-h-[1.5rem] max-h-48 overflow-y-auto"
        @keydown="onKeydown"
        @input="autoResize"
      />

      <!-- Char count -->
      <span
        v-if="charCount > MAX_CHARS * 0.8"
        class="text-xs flex-shrink-0"
        :class="overLimit ? 'text-red-500' : 'text-gray-400'"
      >
        {{ MAX_CHARS - charCount }}
      </span>

      <!-- Send button -->
      <button
        :disabled="!body.trim() || sending || overLimit"
        class="p-1.5 bg-brand-500 text-white rounded-lg hover:bg-brand-600 disabled:opacity-40 disabled:cursor-not-allowed transition-colors flex-shrink-0"
        @click="send"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
        </svg>
      </button>
    </div>

    <!-- Click outside to close emoji picker -->
    <div
      v-if="showEmojiPicker"
      class="fixed inset-0 z-40"
      @click="showEmojiPicker = false"
    />
  </div>
</template>
