import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/lib/api'
import type { Channel, Message } from '@/types'

export const useMessageStore = defineStore('messages', () => {
  const channels = ref<Channel[]>([])
  const currentChannel = ref<Channel | null>(null)
  const messages = ref<Message[]>([])
  const loading = ref(false)
  const cursor = ref<string | null>(null)
  const hasMore = ref(true)

  const sortedMessages = computed(() =>
    [...messages.value].sort(
      (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
    )
  )

  const channelById = computed(
    () => (id: string) => channels.value.find((c) => c.id === id) ?? null
  )

  const unreadCount = computed(() =>
    channels.value.reduce((sum, c) => sum + (c.unread_count ?? 0), 0)
  )

  async function fetchChannels(workspaceId: string): Promise<void> {
    const { data } = await api.get(`/api/v1/channels/${workspaceId}`)
    channels.value = data
  }

  async function selectChannel(channel: Channel): Promise<void> {
    currentChannel.value = channel
    messages.value = []
    cursor.value = null
    hasMore.value = true
    await fetchMessages(channel.id)
  }

  async function fetchMessages(channelId: string, beforeCursor?: string): Promise<void> {
    if (!hasMore.value && beforeCursor) return
    loading.value = true
    try {
      const params: Record<string, string> = { limit: '50' }
      if (beforeCursor) params.cursor = beforeCursor
      const { data } = await api.get(`/api/v1/messages/${channelId}`, { params })
      if (beforeCursor) {
        messages.value = [...data.items, ...messages.value]
      } else {
        messages.value = data.items
      }
      cursor.value = data.cursor
      hasMore.value = !!data.cursor
    } finally {
      loading.value = false
    }
  }

  async function sendMessage(
    channelId: string,
    body: string,
    threadId?: string
  ): Promise<void> {
    const { data } = await api.post(`/api/v1/messages/${channelId}`, {
      body,
      thread_id: threadId ?? null,
    })
    if (!threadId) messages.value.push(data)
  }

  async function editMessage(
    channelId: string,
    messageId: string,
    body: string
  ): Promise<void> {
    const { data } = await api.patch(`/api/v1/messages/${channelId}/${messageId}`, { body })
    const idx = messages.value.findIndex((m) => m.id === messageId)
    if (idx !== -1) messages.value[idx] = data
  }

  async function deleteMessage(channelId: string, messageId: string): Promise<void> {
    await api.delete(`/api/v1/messages/${channelId}/${messageId}`)
    messages.value = messages.value.filter((m) => m.id !== messageId)
  }

  async function addReaction(
    channelId: string,
    messageId: string,
    emoji: string
  ): Promise<void> {
    const { data } = await api.post(
      `/api/v1/messages/${channelId}/${messageId}/reactions`,
      { emoji }
    )
    const idx = messages.value.findIndex((m) => m.id === messageId)
    if (idx !== -1) messages.value[idx].reactions = data.reactions
  }

  async function createChannel(
    workspaceId: string,
    name: string,
    type: string
  ): Promise<Channel> {
    const { data } = await api.post(`/api/v1/channels/${workspaceId}`, { name, type })
    channels.value.push(data)
    return data
  }

  async function createDM(workspaceId: string, userId: string): Promise<Channel> {
    const { data } = await api.post('/api/v1/channels/dm', {
      workspace_id: workspaceId,
      user_id: userId,
    })
    if (!channels.value.find((c) => c.id === data.id)) {
      channels.value.push(data)
    }
    return data
  }

  function appendLiveMessage(message: Message): void {
    if (
      message.channel_id === currentChannel.value?.id &&
      !message.thread_id
    ) {
      if (!messages.value.find((m) => m.id === message.id)) {
        messages.value.push(message)
      }
    }
  }

  return {
    channels,
    currentChannel,
    messages,
    loading,
    cursor,
    hasMore,
    sortedMessages,
    channelById,
    unreadCount,
    fetchChannels,
    selectChannel,
    fetchMessages,
    sendMessage,
    editMessage,
    deleteMessage,
    addReaction,
    createChannel,
    createDM,
    appendLiveMessage,
  }
})
