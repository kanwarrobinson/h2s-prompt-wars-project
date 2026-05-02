<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { format } from 'date-fns'
import { useAuthStore } from '@/stores/auth'
import { useTaskStore } from '@/stores/tasks'
import { useWorkspaceStore } from '@/stores/workspace'
import KanbanBoard from '@/components/kanban/KanbanBoard.vue'
import TaskFilters from '@/components/tasks/TaskFilters.vue'
import TaskForm from '@/components/tasks/TaskForm.vue'
import api from '@/lib/api'
import type { Sprint } from '@/types'

const router = useRouter()
const authStore = useAuthStore()
const taskStore = useTaskStore()
const workspaceStore = useWorkspaceStore()

const sprints = ref<Sprint[]>([])
const selectedSprintId = ref<string | null>(null)
const showNewTaskForm = ref(false)
const loadingSprints = ref(false)

const selectedSprint = computed(() =>
  sprints.value.find((s) => s.id === selectedSprintId.value) ?? null
)

const sprintProgress = computed(() => {
  if (!selectedSprint.value) return 0
  const total = taskStore.tasks.length
  if (!total) return 0
  const done = taskStore.tasks.filter((t) => t.status === 'done').length
  return Math.round((done / total) * 100)
})

async function fetchSprints() {
  if (!workspaceStore.currentWorkspaceId) return
  loadingSprints.value = true
  try {
    const { data } = await api.get(
      `/api/v1/sprints/${workspaceStore.currentWorkspaceId}`
    )
    sprints.value = data
    const active = data.find((s: Sprint) => s.status === 'active')
    selectedSprintId.value = active?.id ?? data[0]?.id ?? null
  } finally {
    loadingSprints.value = false
  }
}

async function loadTasks() {
  if (!workspaceStore.currentWorkspaceId) return
  await taskStore.fetchTasks(
    workspaceStore.currentWorkspaceId,
    selectedSprintId.value ?? undefined
  )
}

async function onSprintChange() {
  await loadTasks()
}

async function startSprint() {
  if (!selectedSprint.value || !workspaceStore.currentWorkspaceId) return
  await api.patch(
    `/api/v1/sprints/${workspaceStore.currentWorkspaceId}/${selectedSprint.value.id}`,
    { status: 'active' }
  )
  await fetchSprints()
}

async function completeSprint() {
  if (!selectedSprint.value || !workspaceStore.currentWorkspaceId) return
  await api.patch(
    `/api/v1/sprints/${workspaceStore.currentWorkspaceId}/${selectedSprint.value.id}`,
    { status: 'completed' }
  )
  await fetchSprints()
}

function formatSprintDate(dateStr: string) {
  return format(new Date(dateStr), 'MMM d')
}

onMounted(async () => {
  if (!authStore.isAuthenticated) {
    router.replace('/login')
    return
  }
  await workspaceStore.fetchWorkspaces()
  await fetchSprints()
  await loadTasks()
  if (workspaceStore.currentWorkspaceId) {
    taskStore.subscribeToUpdates(workspaceStore.currentWorkspaceId)
  }
})

onUnmounted(() => {
  taskStore.unsubscribe()
})
</script>

<template>
  <div class="flex flex-col h-full bg-gray-50 dark:bg-surface-dark overflow-hidden">
    <!-- Sprint Header -->
    <div class="bg-white dark:bg-surface-dark-elevated border-b border-gray-200 dark:border-gray-700 px-6 py-4">
      <div class="flex flex-wrap items-center justify-between gap-4">
        <!-- Sprint selector -->
        <div class="flex items-center gap-3">
          <select
            v-model="selectedSprintId"
            class="text-sm border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-1.5 bg-white dark:bg-surface-dark-elevated text-gray-800 dark:text-gray-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
            @change="onSprintChange"
          >
            <option v-if="sprints.length === 0" :value="null">No sprints</option>
            <option
              v-for="sprint in sprints"
              :key="sprint.id"
              :value="sprint.id"
            >
              {{ sprint.name }}
            </option>
          </select>

          <template v-if="selectedSprint">
            <span class="text-sm text-gray-500 dark:text-gray-400">
              {{ formatSprintDate(selectedSprint.start_date) }} –
              {{ formatSprintDate(selectedSprint.end_date) }}
            </span>
            <span class="text-xs font-medium px-2 py-0.5 rounded-full"
              :class="{
                'bg-yellow-100 text-yellow-700': selectedSprint.status === 'planned',
                'bg-green-100 text-green-700': selectedSprint.status === 'active',
                'bg-gray-100 text-gray-600': selectedSprint.status === 'completed',
              }"
            >
              {{ selectedSprint.status }}
            </span>
          </template>
        </div>

        <!-- Sprint info & actions -->
        <div class="flex items-center gap-4">
          <template v-if="selectedSprint">
            <!-- Progress bar -->
            <div class="hidden md:flex items-center gap-2">
              <span class="text-xs text-gray-500">{{ sprintProgress }}%</span>
              <div class="w-32 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                <div
                  class="h-full bg-brand-500 rounded-full transition-all"
                  :style="{ width: `${sprintProgress}%` }"
                />
              </div>
            </div>
            <span class="hidden md:block text-xs text-gray-500">
              Velocity: {{ selectedSprint.velocity }} pts
            </span>
            <button
              v-if="selectedSprint.status === 'planned'"
              class="px-3 py-1.5 text-sm bg-brand-500 text-white rounded-lg hover:bg-brand-600 transition-colors"
              @click="startSprint"
            >
              Start Sprint
            </button>
            <button
              v-else-if="selectedSprint.status === 'active'"
              class="px-3 py-1.5 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
              @click="completeSprint"
            >
              Complete Sprint
            </button>
          </template>

          <button
            class="px-3 py-1.5 text-sm bg-brand-500 text-white rounded-lg hover:bg-brand-600 transition-colors"
            @click="showNewTaskForm = true"
          >
            + New Task
          </button>
        </div>
      </div>

      <!-- Filters -->
      <div class="mt-3">
        <TaskFilters />
      </div>
    </div>

    <!-- Kanban Board -->
    <div class="flex-1 overflow-hidden">
      <KanbanBoard v-if="workspaceStore.currentWorkspaceId" />
      <div v-else class="flex items-center justify-center h-full text-gray-400">
        Select a workspace to view the board
      </div>
    </div>

    <!-- New Task Modal -->
    <Teleport to="body">
      <div
        v-if="showNewTaskForm"
        class="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4"
        @click.self="showNewTaskForm = false"
      >
        <div class="bg-white dark:bg-surface-dark-elevated rounded-2xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
          <div class="p-6">
            <div class="flex items-center justify-between mb-4">
              <h2 class="text-lg font-semibold text-gray-900 dark:text-white">New Task</h2>
              <button
                class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
                @click="showNewTaskForm = false"
              >
                ✕
              </button>
            </div>
            <TaskForm
              :sprint-id="selectedSprintId ?? undefined"
              @saved="showNewTaskForm = false"
              @cancel="showNewTaskForm = false"
            />
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>
