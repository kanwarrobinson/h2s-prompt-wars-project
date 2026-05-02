<script setup lang="ts">
import { ref } from 'vue'
import draggable from 'vuedraggable'
import TaskCard from './TaskCard.vue'
import TaskDetail from '@/components/tasks/TaskDetail.vue'
import { useTaskStore } from '@/stores/tasks'
import { TASK_STATUS_LABELS, TASK_STATUS_COLORS } from '@/lib/constants'
import type { TaskStatus, Task } from '@/types'

const props = defineProps<{
  status: TaskStatus
  tasks: Task[]
  workspaceId: string
}>()

const taskStore = useTaskStore()
const selectedTask = ref<Task | null>(null)
const showAddTask = ref(false)
const newTaskTitle = ref('')

const statusDotColors: Record<TaskStatus, string> = {
  backlog: 'bg-gray-400',
  todo: 'bg-blue-500',
  in_progress: 'bg-yellow-500',
  review: 'bg-purple-500',
  done: 'bg-green-500',
}

async function onDragChange(event: { added?: { element: Task }; removed?: { element: Task } }) {
  if (event.added) {
    await taskStore.moveTask(props.workspaceId, event.added.element.id, props.status)
  }
}

async function addQuickTask() {
  const title = newTaskTitle.value.trim()
  if (!title) return
  await taskStore.createTask(props.workspaceId, {
    title,
    status: props.status,
    priority: 'medium',
    type: 'task',
  })
  newTaskTitle.value = ''
  showAddTask.value = false
}
</script>

<template>
  <div class="flex flex-col w-72 flex-shrink-0 bg-gray-100 dark:bg-gray-800/50 rounded-xl">
    <!-- Column header -->
    <div class="flex items-center justify-between px-4 py-3">
      <div class="flex items-center gap-2">
        <span class="w-2.5 h-2.5 rounded-full" :class="statusDotColors[status]" />
        <span class="text-sm font-semibold text-gray-700 dark:text-gray-300">
          {{ TASK_STATUS_LABELS[status] }}
        </span>
        <span class="text-xs bg-gray-200 dark:bg-gray-700 text-gray-500 dark:text-gray-400 rounded-full px-2 py-0.5 font-medium">
          {{ tasks.length }}
        </span>
      </div>
    </div>

    <!-- Task list (draggable) -->
    <draggable
      :list="tasks"
      group="tasks"
      item-key="id"
      class="flex flex-col gap-2 px-3 pb-2 min-h-[2rem] flex-1 overflow-y-auto"
      ghost-class="opacity-40"
      @change="onDragChange"
    >
      <template #item="{ element }">
        <TaskCard
          :task="element"
          @click="selectedTask = element"
        />
      </template>
    </draggable>

    <!-- Add task -->
    <div class="px-3 pb-3">
      <div v-if="showAddTask" class="bg-white dark:bg-surface-dark-elevated rounded-lg p-2 shadow-sm">
        <input
          v-model="newTaskTitle"
          type="text"
          placeholder="Task title"
          class="w-full text-sm bg-transparent text-gray-800 dark:text-gray-200 placeholder-gray-400 focus:outline-none"
          autofocus
          @keydown.enter="addQuickTask"
          @keydown.escape="showAddTask = false; newTaskTitle = ''"
        />
        <div class="flex gap-2 mt-2">
          <button
            class="px-3 py-1 text-xs bg-brand-500 text-white rounded-md hover:bg-brand-600 transition-colors"
            @click="addQuickTask"
          >
            Add
          </button>
          <button
            class="px-3 py-1 text-xs text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 transition-colors"
            @click="showAddTask = false; newTaskTitle = ''"
          >
            Cancel
          </button>
        </div>
      </div>
      <button
        v-else
        class="w-full flex items-center gap-1 px-2 py-1.5 text-sm text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg transition-colors"
        @click="showAddTask = true"
      >
        <span class="text-lg leading-none">+</span>
        <span>Add task</span>
      </button>
    </div>
  </div>

  <!-- Task detail modal -->
  <Teleport to="body">
    <div
      v-if="selectedTask"
      class="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4"
      @click.self="selectedTask = null"
    >
      <div class="bg-white dark:bg-surface-dark-elevated rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <TaskDetail
          :task="selectedTask"
          :workspace-id="workspaceId"
          @close="selectedTask = null"
          @updated="selectedTask = null"
        />
      </div>
    </div>
  </Teleport>
</template>
