import { ref, onUnmounted } from 'vue'
import {
  onSnapshot,
  type Query,
  type DocumentData,
  type Unsubscribe,
} from 'firebase/firestore'

export function useFirestoreCollection<T>(q: Query<DocumentData>) {
  const items = ref<T[]>([])
  const loading = ref(true)
  const error = ref<Error | null>(null)

  let unsubscribe: Unsubscribe | null = null

  function start(): void {
    unsubscribe = onSnapshot(
      q,
      (snapshot) => {
        items.value = snapshot.docs.map((d) => ({ id: d.id, ...d.data() }) as T)
        loading.value = false
      },
      (err) => {
        error.value = err
        loading.value = false
      }
    )
  }

  function stop(): void {
    unsubscribe?.()
  }

  onUnmounted(stop)

  return { items, loading, error, start, stop }
}
