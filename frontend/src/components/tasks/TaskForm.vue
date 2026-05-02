<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useTaskStore } from '@/stores/tasks'
import { useWorkspaceStore } from '@/stores/workspace'
import type { TaskType, TaskStatus, TaskPriority } from '@/types'
import api from '@/lib/api'

const props = defineProps<{
  sprintId?: string
}>()

const emit = defineEmits<{
  saved: []
  cancel: []
}>()

const taskStore = useTaskStore()
const workspaceStore = useWorkspaceStore()

const submitting = ref(false)
const error = ref<string | null>(null)
const labelsInput = ref('')

interface FormState {
  title: string
  type: TaskType
  status: TaskStatus
  priority: TaskPriority
  description: string
  sprint_id: string
  assignee_ids: string[]
  story_points: string
}

const form = reactive<FormState>({
  title: '',
  type: 'task',
  status: 'todo',
  priority: 'medium',
  description: '',
  sprint_id: props.sprintId ?? '',
  assignee_ids: [],
  story_points: '',
})

const types: { value: TaskType; label: string }[] = [
  { value: 'task', label: '✅ Task' },
  { value: 'bug', label: '🐛 Bug' },
  { value: 'story', label: '📖 Story' },
  { value: 'epic', label: '⚡ Epic' },
]

const statuses: { value: TaskStatus; label: string }[] = [
  { value: 'backlog', label: 'Backlog' },
  { value: 'todo', label: 'To Do' },
  { value: 'in_progress', label: 'In Progress' },
  { value: 'review', label: 'In Review' },
  { value: 'done', label: 'Done' },
]

const priorities: { value: TaskPriority; label: string }[] = [
  { value: 'low', label: 'Low' },
  { value: 'medium', label: 'Medium' },
  { value: 'high', label: 'High' },
  { value: 'critical', label: 'Critical' },
]

async function submit() {
  if (!form.title.trim()) {
    error.value = 'Title is required.'
    return
  }
  const wsId = workspaceStore.currentWorkspaceId
  if (!wsId) return

  submitting.value = true
  error.value = null
  try {
    const labels = labelsInput.value
      .split(',')
      .map((l) => l.trim())
      .filter(Boolean)

    await taskStore.createTask(wsId, {
      title: form.title.trim(),
      type: form.type,
      status: form.status,
      priority: form.priority,
      description: form.description,
      sprint_id: form.sprint_id || null,
      assignee_ids: form.assignee_ids,
      story_points: form.story_points ? Number(form.story_points) : null,
      labels,
    })
    emit('saved')
  } catch (e: unknown) {
    error.value = (e as Error).message ?? 'Failed to create task'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <form class="space-y-4" @submit.prevent="submit">
    <!-- Error -->
    <div v-if="error" class="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-sm text-red-700 dark:text-red-400">
      {{ error }}
    </div>

    <!-- Title -->
    <div>
      <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
        Title <span class="text-red-500">*</span>
      </label>
      <input
        v-model="form.title"
        type="text"
        placeholder="Task title"
        class="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-surface-dark text-gray-800 dark:text-gray-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
        required
      />
    </div>

    <!-- Type + Priority row -->
    <div class="grid grid-cols-2 gap-3">
      <div>
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Type</label>
        <select
          v-model="form.type"
          class="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-surface-dark text-gray-800 dark:text-gray-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
        >
          <option v-for="t in types" :key="t.value" :value="t.value">{{ t.label }}</option>
        </select>
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Priority</label>
        <select
          v-model="form.priority"
          class="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-surface-dark text-gray-800 dark:text-gray-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
        >
          <option v-for="p in priorities" :key="p.value" :value="p.value">{{ p.label }}</option>
        </select>
      </div>
    </div>

    <!-- Status -->
    <div>
      <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Status</label>
      <select
        v-model="form.status"
        class="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-surface-dark text-gray-800 dark:text-gray-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
      >
        <option v-for="s in statuses" :key="s.value" :value="s.value">{{ s.label }}</option>
      </select>
    </div>

    <!-- Labels -->
    <div>
      <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
        Labels
        <span class="text-xs font-normal text-gray-400">(comma-separated)</span>
      </label>
      <input
        v-model="labelsInput"
        type="text"
        placeholder="frontend, bug, urgent"
        class="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-surface-dark text-gray-800 dark:text-gray-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
      />
    </div>

    <!-- Description -->
    <div>
      <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Description</label>
      <textarea
        v-model="form.description"
        rows="3"
        placeholder="Describe the task…"
        class="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-surface-dark text-gray-800 dark:text-gray-200 focus:outline-none focus:ring-2 focus:ring-brand-500 resize-none"
      />
    </div>

    <!-- Story points -->
    <div>
      <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Story Points</label>
      <input
        v-model="form.story_points"
        type="number"
        min="0"
        max="100"
        placeholder="0"
        class="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-surface-dark text-gray-800 dark:text-gray-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
      />
    </div>

    <!-- Actions -->
    <div class="flex gap-3 pt-2">
      <button
        type="submit"
        :disabled="submitting"
        class="flex-1 py-2 bg-brand-500 text-white text-sm font-medium rounded-lg hover:bg-brand-600 disabled:opacity-50 transition-colors"
      >
        {{ submitting ? 'Creating…' : 'Create Task' }}
      </button>
      <button
        type="button"
        class="px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 text-sm font-medium rounded-lg hover:bg-gray-50 dark:hover:bg-white/5 transition-colors"
        @click="emit('cancel')"
      >
        Cancel
      </button>
    </div>
  </form>
</template>
