import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { collection, onSnapshot, query } from 'firebase/firestore'
import { db as firestoreDb } from '@/lib/firebase'
import api from '@/lib/api'
import type { Task, TaskStatus } from '@/types'
import type { Unsubscribe } from 'firebase/firestore'

export const useTaskStore = defineStore('tasks', () => {
  const tasks = ref<Task[]>([])
  const currentTask = ref<Task | null>(null)
  const loading = ref(false)
  const filters = ref({ assignee: '', priority: '', label: '' })
  let _unsubscribe: Unsubscribe | null = null

  const tasksByStatus = computed(() => {
    const grouped: Record<TaskStatus, Task[]> = {
      backlog: [],
      todo: [],
      in_progress: [],
      review: [],
      done: [],
    }
    for (const t of tasks.value) {
      grouped[t.status]?.push(t)
    }
    return grouped
  })

  const tasksByAssignee = computed(() => (userId: string) =>
    tasks.value.filter((t) => t.assignee_ids.includes(userId))
  )

  async function fetchTasks(workspaceId: string, sprintId?: string): Promise<void> {
    loading.value = true
    try {
      const params: Record<string, string> = {}
      if (sprintId) params.sprint_id = sprintId
      const { data } = await api.get(`/api/v1/tasks/${workspaceId}`, { params })
      tasks.value = data
    } finally {
      loading.value = false
    }
  }

  async function createTask(workspaceId: string, payload: Partial<Task>): Promise<Task> {
    const { data } = await api.post(`/api/v1/tasks/${workspaceId}`, payload)
    tasks.value.unshift(data)
    return data
  }

  async function updateTask(
    workspaceId: string,
    taskId: string,
    payload: Partial<Task>
  ): Promise<void> {
    const { data } = await api.patch(`/api/v1/tasks/${workspaceId}/${taskId}`, payload)
    const idx = tasks.value.findIndex((t) => t.id === taskId)
    if (idx !== -1) tasks.value[idx] = data
    if (currentTask.value?.id === taskId) currentTask.value = data
  }

  async function moveTask(
    workspaceId: string,
    taskId: string,
    newStatus: TaskStatus
  ): Promise<void> {
    const task = tasks.value.find((t) => t.id === taskId)
    const previousStatus = task?.status
    if (task) task.status = newStatus
    try {
      await api.patch(`/api/v1/tasks/${workspaceId}/${taskId}`, { status: newStatus })
    } catch {
      if (task && previousStatus) task.status = previousStatus
    }
  }

  async function deleteTask(workspaceId: string, taskId: string): Promise<void> {
    await api.delete(`/api/v1/tasks/${workspaceId}/${taskId}`)
    tasks.value = tasks.value.filter((t) => t.id !== taskId)
  }

  async function addComment(
    workspaceId: string,
    taskId: string,
    body: string
  ): Promise<void> {
    const { data } = await api.post(
      `/api/v1/tasks/${workspaceId}/${taskId}/comments`,
      { body }
    )
    const task = tasks.value.find((t) => t.id === taskId)
    if (task) task.comments = data.comments
  }

  function subscribeToUpdates(workspaceId: string): void {
    if (_unsubscribe) _unsubscribe()
    const q = query(
      collection(firestoreDb, `workspaces/${workspaceId}/task_updates`)
    )
    _unsubscribe = onSnapshot(q, (snapshot) => {
      snapshot.docChanges().forEach((change) => {
        const updated = change.doc.data()
        const idx = tasks.value.findIndex((t) => t.id === change.doc.id)
        if (idx !== -1) {
          tasks.value[idx] = { ...tasks.value[idx], ...updated } as Task
        }
      })
    })
  }

  function unsubscribe(): void {
    _unsubscribe?.()
    _unsubscribe = null
  }

  return {
    tasks,
    currentTask,
    loading,
    filters,
    tasksByStatus,
    tasksByAssignee,
    fetchTasks,
    createTask,
    updateTask,
    moveTask,
    deleteTask,
    addComment,
    subscribeToUpdates,
    unsubscribe,
  }
})
