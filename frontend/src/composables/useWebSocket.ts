import { ref, onUnmounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import {
  WEBSOCKET_RECONNECT_BASE_MS,
  WEBSOCKET_RECONNECT_MAX_MS,
  PRESENCE_HEARTBEAT_MS,
} from '@/lib/constants'

export function useWebSocket(workspaceId: string) {
  const ws = ref<WebSocket | null>(null)
  const connected = ref(false)
  const messages = ref<unknown[]>([])
  const authStore = useAuthStore()

  let reconnectDelay = WEBSOCKET_RECONNECT_BASE_MS
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null
  let heartbeatTimer: ReturnType<typeof setInterval> | null = null
  let destroyed = false

  function connect(): void {
    if (destroyed) return
    const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8002'
    const socket = new WebSocket(`${wsUrl}/ws/${workspaceId}`)

    socket.onopen = () => {
      connected.value = true
      reconnectDelay = WEBSOCKET_RECONNECT_BASE_MS
      socket.send(JSON.stringify({ type: 'auth', token: authStore.token }))
      heartbeatTimer = setInterval(() => {
        if (socket.readyState === WebSocket.OPEN) {
          socket.send(JSON.stringify({ type: 'ping' }))
        }
      }, PRESENCE_HEARTBEAT_MS)
    }

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data as string) as unknown
        if ((data as Record<string, unknown>).type !== 'pong') {
          messages.value.push(data)
        }
      } catch {
        // ignore malformed messages
      }
    }

    socket.onclose = () => {
      connected.value = false
      if (heartbeatTimer !== null) clearInterval(heartbeatTimer)
      if (!destroyed) {
        reconnectTimer = setTimeout(() => {
          reconnectDelay = Math.min(reconnectDelay * 2, WEBSOCKET_RECONNECT_MAX_MS)
          connect()
        }, reconnectDelay)
      }
    }

    socket.onerror = () => {
      socket.close()
    }

    ws.value = socket
  }

  function send(payload: object): void {
    if (ws.value?.readyState === WebSocket.OPEN) {
      ws.value.send(JSON.stringify(payload))
    }
  }

  function sendTyping(channelId: string): void {
    send({ type: 'typing', channel_id: channelId })
  }

  function disconnect(): void {
    destroyed = true
    if (reconnectTimer !== null) clearTimeout(reconnectTimer)
    if (heartbeatTimer !== null) clearInterval(heartbeatTimer)
    ws.value?.close()
  }

  connect()
  onUnmounted(disconnect)

  return { ws, connected, messages, send, sendTyping, disconnect }
}
