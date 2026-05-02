<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { format, isToday, isPast } from 'date-fns'
import { useAuthStore } from '@/stores/auth'
import { useTaskStore } from '@/stores/tasks'
import { useWorkspaceStore } from '@/stores/workspace'
import { TASK_PRIORITY_LABELS, TASK_PRIORITY_COLORS } from '@/lib/constants'
import type { Task } from '@/types'

const router = useRouter()
const authStore = useAuthStore()
const taskStore = useTaskStore()
const workspaceStore = useWorkspaceStore()

const showNewTaskModal = ref(false)

const myTasks = computed(() => {
  const uid = authStore.profile?.id
  if (!uid) return []
  return taskStore.tasks.filter(
    (t) => t.assignee_ids.includes(uid) && t.status !== 'done'
  )
})

const tasksDueToday = computed(() =>
  taskStore.tasks.filter(
    (t) => t.due_date && isToday(new Date(t.due_date)) && t.status !== 'done'
  )
)

const openTasks = computed(() =>
  taskStore.tasks.filter((t) => t.status !== 'done')
)

const recentTasks = computed(() =>
  [...taskStore.tasks]
    .sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime())
    .slice(0, 10)
)

const myTasksByPriority = computed(() => {
  const groups: Record<string, Task[]> = {
    critical: [],
    high: [],
    medium: [],
    low: [],
  }
  for (const t of myTasks.value) {
    groups[t.priority]?.push(t)
  }
  return groups
})

function formatDate(dateStr: string) {
  return format(new Date(dateStr), 'MMM d')
}

function isOverdue(task: Task) {
  return task.due_date && isPast(new Date(task.due_date)) && task.status !== 'done'
}

onMounted(async () => {
  if (!authStore.isAuthenticated) {
    router.replace('/login')
    return
  }
  await workspaceStore.fetchWorkspaces()
  if (workspaceStore.currentWorkspaceId) {
    await taskStore.fetchTasks(workspaceStore.currentWorkspaceId)
  }
})
</script>

<template>
  <div class="flex-1 overflow-y-auto p-6 bg-gray-50 dark:bg-surface-dark">
    <!-- Header -->
    <div class="mb-8">
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
        Good {{ new Date().getHours() < 12 ? 'morning' : new Date().getHours() < 18 ? 'afternoon' : 'evening' }},
        {{ authStore.displayName }} 👋
      </h1>
      <p class="text-gray-500 dark:text-gray-400 mt-1">Here's what's happening today.</p>
    </div>

    <!-- Loading skeleton -->
    <div v-if="taskStore.loading" class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
      <div
        v-for="i in 3"
        :key="i"
        class="h-28 bg-white dark:bg-surface-dark-elevated rounded-xl animate-pulse"
      />
    </div>

    <!-- Stats cards -->
    <div v-else class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
      <div class="bg-white dark:bg-surface-dark-elevated rounded-xl p-6 shadow-sm">
        <p class="text-sm text-gray-500 dark:text-gray-400 mb-1">Open Tasks</p>
        <p class="text-3xl font-bold text-gray-900 dark:text-white">{{ openTasks.length }}</p>
        <p class="text-xs text-gray-400 mt-1">across all projects</p>
      </div>
      <div class="bg-white dark:bg-surface-dark-elevated rounded-xl p-6 shadow-sm">
        <p class="text-sm text-gray-500 dark:text-gray-400 mb-1">Due Today</p>
        <p class="text-3xl font-bold text-orange-500">{{ tasksDueToday.length }}</p>
        <p class="text-xs text-gray-400 mt-1">tasks need attention</p>
      </div>
      <div class="bg-white dark:bg-surface-dark-elevated rounded-xl p-6 shadow-sm">
        <p class="text-sm text-gray-500 dark:text-gray-400 mb-1">Assigned to Me</p>
        <p class="text-3xl font-bold text-brand-500">{{ myTasks.length }}</p>
        <p class="text-xs text-gray-400 mt-1">active tasks</p>
      </div>
    </div>

    <!-- Quick Actions -->
    <div class="flex gap-3 mb-8">
      <button
        class="flex items-center gap-2 px-4 py-2 bg-brand-500 text-white rounded-lg hover:bg-brand-600 transition-colors text-sm font-medium"
        @click="showNewTaskModal = true"
      >
        <span>+</span> New Task
      </button>
      <button
        class="flex items-center gap-2 px-4 py-2 bg-white dark:bg-surface-dark-elevated border border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-white/5 transition-colors text-sm font-medium"
        @click="router.push('/channels/general')"
      >
        <span>#</span> New Channel
      </button>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- My Tasks -->
      <div class="bg-white dark:bg-surface-dark-elevated rounded-xl shadow-sm p-6">
        <h2 class="font-semibold text-gray-900 dark:text-white mb-4">My Tasks</h2>
        <div v-if="myTasks.length === 0" class="text-gray-400 text-sm">
          No tasks assigned to you 🎉
        </div>
        <div v-else class="space-y-4">
          <div
            v-for="[priority, pts] in Object.entries(myTasksByPriority).filter(([, t]) => t.length)"
            :key="priority"
          >
            <p
              class="text-xs font-semibold uppercase tracking-wide mb-2"
              :class="TASK_PRIORITY_COLORS[priority as keyof typeof TASK_PRIORITY_COLORS]"
            >
              {{ TASK_PRIORITY_LABELS[priority as keyof typeof TASK_PRIORITY_LABELS] }}
            </p>
            <div class="space-y-2">
              <div
                v-for="task in pts"
                :key="task.id"
                class="flex items-center justify-between p-3 rounded-lg bg-gray-50 dark:bg-white/5 cursor-pointer hover:bg-gray-100 dark:hover:bg-white/10 transition-colors"
                @click="router.push(`/board?task=${task.id}`)"
              >
                <span class="text-sm text-gray-800 dark:text-gray-200 truncate flex-1">
                  {{ task.title }}
                </span>
                <span
                  v-if="task.due_date"
                  class="text-xs ml-2 flex-shrink-0"
                  :class="isOverdue(task) ? 'text-red-500 font-medium' : 'text-gray-400'"
                >
                  {{ formatDate(task.due_date) }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Recent Activity -->
      <div class="bg-white dark:bg-surface-dark-elevated rounded-xl shadow-sm p-6">
        <h2 class="font-semibold text-gray-900 dark:text-white mb-4">Recent Activity</h2>
        <div v-if="recentTasks.length === 0" class="text-gray-400 text-sm">
          No recent activity.
        </div>
        <div v-else class="space-y-3">
          <div
            v-for="task in recentTasks"
            :key="task.id"
            class="flex items-start gap-3 p-2 rounded-lg hover:bg-gray-50 dark:hover:bg-white/5 cursor-pointer transition-colors"
            @click="router.push(`/board?task=${task.id}`)"
          >
            <div class="w-2 h-2 mt-2 rounded-full bg-brand-500 flex-shrink-0" />
            <div class="flex-1 min-w-0">
              <p class="text-sm text-gray-800 dark:text-gray-200 truncate">{{ task.title }}</p>
              <p class="text-xs text-gray-400 mt-0.5">
                Updated {{ formatDate(task.updated_at) }}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
