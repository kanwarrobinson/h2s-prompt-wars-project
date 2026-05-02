import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  collection,
  query,
  onSnapshot,
  doc,
  setDoc,
} from 'firebase/firestore'
import { db as firestoreDb } from '@/lib/firebase'
import type { PresenceStatus } from '@/types'
import type { Unsubscribe } from 'firebase/firestore'

export const usePresenceStore = defineStore('presence', () => {
  const presenceMap = ref<Record<string, PresenceStatus>>({})
  let _unsubscribe: Unsubscribe | null = null

  const isOnline = computed(() => (userId: string) =>
    presenceMap.value[userId] === 'online'
  )

  const getStatus = computed(
    () =>
      (userId: string): PresenceStatus =>
        presenceMap.value[userId] ?? 'offline'
  )

  async function updateMyPresence(
    workspaceId: string,
    userId: string,
    status: PresenceStatus
  ): Promise<void> {
    presenceMap.value[userId] = status
    try {
      const docRef = doc(firestoreDb, `workspaces/${workspaceId}/presence/${userId}`)
      await setDoc(
        docRef,
        { status, last_seen: new Date().toISOString() },
        { merge: true }
      )
    } catch {
      // non-fatal
    }
  }

  function subscribeToPresence(workspaceId: string): void {
    if (_unsubscribe) _unsubscribe()
    const q = query(collection(firestoreDb, `workspaces/${workspaceId}/presence`))
    _unsubscribe = onSnapshot(q, (snap) => {
      snap.forEach((d) => {
        const data = d.data()
        presenceMap.value[d.id] = (data.status as PresenceStatus) ?? 'offline'
      })
    })
  }

  function unsubscribe(): void {
    _unsubscribe?.()
    _unsubscribe = null
  }

  return {
    presenceMap,
    isOnline,
    getStatus,
    updateMyPresence,
    subscribeToPresence,
    unsubscribe,
  }
})
