import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useTasksStore } from '@/stores/tasks'

vi.mock('@/lib/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() },
    },
    defaults: { headers: { common: {} } },
  },
  setAuthToken: vi.fn(),
}))

vi.mock('@/lib/firebase', () => ({
  db: {},
}))

vi.mock('firebase/firestore', () => ({
  collection: vi.fn(),
  doc: vi.fn(),
  onSnapshot: vi.fn(() => vi.fn()),
  query: vi.fn(),
  where: vi.fn(),
}))

const mockTasks = [
  { id: 'task-1', title: 'Task 1', status: 'todo', priority: 'medium', workspace_id: 'ws-1', type: 'task', assignee_ids: [] },
  { id: 'task-2', title: 'Task 2', status: 'in_progress', priority: 'high', workspace_id: 'ws-1', type: 'bug', assignee_ids: [] },
  { id: 'task-3', title: 'Task 3', status: 'done', priority: 'low', workspace_id: 'ws-1', type: 'task', assignee_ids: [] },
]

describe('useTasksStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('starts with empty tasks list', () => {
    const store = useTasksStore()
    expect(store.tasks).toEqual([])
  })

  it('fetchTasks populates the tasks list', async () => {
    const api = await import('@/lib/api')
    vi.mocked(api.default.get).mockResolvedValueOnce({ data: mockTasks })

    const store = useTasksStore()
    await store.fetchTasks('ws-1')
    expect(store.tasks).toHaveLength(3)
  })

  it('tasksByStatus groups tasks correctly', async () => {
    const api = await import('@/lib/api')
    vi.mocked(api.default.get).mockResolvedValueOnce({ data: mockTasks })

    const store = useTasksStore()
    await store.fetchTasks('ws-1')

    const byStatus = store.tasksByStatus
    expect(byStatus['todo']).toHaveLength(1)
    expect(byStatus['in_progress']).toHaveLength(1)
    expect(byStatus['done']).toHaveLength(1)
  })

  it('moveTask updates task status optimistically', async () => {
    const api = await import('@/lib/api')
    vi.mocked(api.default.get).mockResolvedValueOnce({ data: mockTasks })
    vi.mocked(api.default.patch).mockResolvedValueOnce({
      data: { ...mockTasks[0], status: 'in_progress' },
    })

    const store = useTasksStore()
    await store.fetchTasks('ws-1')
    await store.moveTask('task-1', 'in_progress')

    const task = store.tasks.find(t => t.id === 'task-1')
    expect(task?.status).toBe('in_progress')
  })

  it('createTask adds task to the list', async () => {
    const api = await import('@/lib/api')
    const newTask = { id: 'task-4', title: 'New task', status: 'backlog', workspace_id: 'ws-1', type: 'task', priority: 'medium', assignee_ids: [] }
    vi.mocked(api.default.post).mockResolvedValueOnce({ data: newTask })

    const store = useTasksStore()
    await store.createTask({ title: 'New task', workspace_id: 'ws-1', type: 'task' } as any)
    expect(store.tasks.find(t => t.id === 'task-4')).toBeDefined()
  })
})
