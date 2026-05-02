import type { TaskStatus, TaskPriority, TaskType } from '@/types'

export const TASK_STATUS_LABELS: Record<TaskStatus, string> = {
  backlog: 'Backlog',
  todo: 'To Do',
  in_progress: 'In Progress',
  review: 'In Review',
  done: 'Done',
}

export const TASK_STATUS_COLORS: Record<TaskStatus, string> = {
  backlog: 'bg-gray-100 text-gray-600',
  todo: 'bg-blue-100 text-blue-700',
  in_progress: 'bg-yellow-100 text-yellow-700',
  review: 'bg-purple-100 text-purple-700',
  done: 'bg-green-100 text-green-700',
}

export const TASK_PRIORITY_COLORS: Record<TaskPriority, string> = {
  low: 'text-gray-400',
  medium: 'text-blue-500',
  high: 'text-orange-500',
  critical: 'text-red-600',
}

export const TASK_PRIORITY_LABELS: Record<TaskPriority, string> = {
  low: 'Low',
  medium: 'Medium',
  high: 'High',
  critical: 'Critical',
}

export const TASK_TYPE_ICONS: Record<TaskType, string> = {
  task: '✅',
  bug: '🐛',
  story: '📖',
  epic: '⚡',
}

export const KANBAN_COLUMNS: TaskStatus[] = [
  'backlog', 'todo', 'in_progress', 'review', 'done',
]

export const MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024 // 50MB
export const WEBSOCKET_RECONNECT_BASE_MS = 2000
export const WEBSOCKET_RECONNECT_MAX_MS = 30000
export const PRESENCE_HEARTBEAT_MS = 25000
