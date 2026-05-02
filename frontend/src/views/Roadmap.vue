<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  startOfQuarter,
  endOfQuarter,
  addQuarters,
  subQuarters,
  eachWeekOfInterval,
  format,
  differenceInDays,
  parseISO,
  isSameDay,
} from 'date-fns'
import { useAuthStore } from '@/stores/auth'
import { useWorkspaceStore } from '@/stores/workspace'
import { useTaskStore } from '@/stores/tasks'
import api from '@/lib/api'
import type { Sprint, Project } from '@/types'

const router = useRouter()
const authStore = useAuthStore()
const workspaceStore = useWorkspaceStore()
const taskStore = useTaskStore()

const sprints = ref<Sprint[]>([])
const projects = ref<Project[]>([])
const selectedProjectId = ref<string | null>(null)
const currentQuarterStart = ref(startOfQuarter(new Date()))
const loading = ref(false)

const currentQuarterEnd = computed(() => endOfQuarter(currentQuarterStart.value))

const weeks = computed(() =>
  eachWeekOfInterval(
    { start: currentQuarterStart.value, end: currentQuarterEnd.value },
    { weekStartsOn: 1 }
  )
)

const quarterLabel = computed(
  () => `Q${Math.floor(currentQuarterStart.value.getMonth() / 3) + 1} ${format(currentQuarterStart.value, 'yyyy')}`
)

const filteredSprints = computed(() =>
  selectedProjectId.value
    ? sprints.value.filter((s) => s.project_id === selectedProjectId.value)
    : sprints.value
)

const totalDays = computed(() =>
  differenceInDays(currentQuarterEnd.value, currentQuarterStart.value) + 1
)

function sprintStyle(sprint: Sprint) {
  const start = parseISO(sprint.start_date)
  const end = parseISO(sprint.end_date)
  const quarterStart = currentQuarterStart.value

  const startOffset = Math.max(0, differenceInDays(start, quarterStart))
  const endOffset = Math.min(
    totalDays.value,
    differenceInDays(end, quarterStart) + 1
  )
  const width = endOffset - startOffset

  return {
    left: `${(startOffset / totalDays.value) * 100}%`,
    width: `${(width / totalDays.value) * 100}%`,
  }
}

function sprintColor(sprint: Sprint) {
  if (sprint.status === 'active') return 'bg-brand-500'
  if (sprint.status === 'completed') return 'bg-green-500'
  return 'bg-gray-300 dark:bg-gray-600'
}

function prevQuarter() {
  currentQuarterStart.value = startOfQuarter(subQuarters(currentQuarterStart.value, 1))
}

function nextQuarter() {
  currentQuarterStart.value = startOfQuarter(addQuarters(currentQuarterStart.value, 1))
}

function getEpicsForSprint(sprintId: string) {
  return taskStore.tasks.filter(
    (t) => t.sprint_id === sprintId && t.type === 'epic'
  )
}

onMounted(async () => {
  if (!authStore.isAuthenticated) {
    router.replace('/login')
    return
  }
  await workspaceStore.fetchWorkspaces()
  if (!workspaceStore.currentWorkspaceId) return

  loading.value = true
  try {
    const [sprintsRes, projectsRes] = await Promise.all([
      api.get(`/api/v1/sprints/${workspaceStore.currentWorkspaceId}`),
      api.get(`/api/v1/projects/${workspaceStore.currentWorkspaceId}`),
    ])
    sprints.value = sprintsRes.data
    projects.value = projectsRes.data
    await taskStore.fetchTasks(workspaceStore.currentWorkspaceId)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="flex flex-col h-full bg-gray-50 dark:bg-surface-dark overflow-hidden">
    <!-- Header -->
    <div class="bg-white dark:bg-surface-dark-elevated border-b border-gray-200 dark:border-gray-700 px-6 py-4">
      <div class="flex items-center justify-between flex-wrap gap-3">
        <h1 class="text-xl font-bold text-gray-900 dark:text-white">Roadmap</h1>

        <!-- Project tabs -->
        <div class="flex items-center gap-2">
          <button
            class="px-3 py-1.5 text-sm rounded-lg transition-colors"
            :class="
              selectedProjectId === null
                ? 'bg-brand-500 text-white'
                : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-white/5'
            "
            @click="selectedProjectId = null"
          >
            All
          </button>
          <button
            v-for="project in projects"
            :key="project.id"
            class="px-3 py-1.5 text-sm rounded-lg transition-colors"
            :class="
              selectedProjectId === project.id
                ? 'bg-brand-500 text-white'
                : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-white/5'
            "
            @click="selectedProjectId = project.id"
          >
            {{ project.name }}
          </button>
        </div>

        <!-- Quarter navigation -->
        <div class="flex items-center gap-3">
          <button
            class="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-white/5 text-gray-500 dark:text-gray-400"
            @click="prevQuarter"
          >
            ←
          </button>
          <span class="text-sm font-medium text-gray-700 dark:text-gray-300 w-20 text-center">
            {{ quarterLabel }}
          </span>
          <button
            class="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-white/5 text-gray-500 dark:text-gray-400"
            @click="nextQuarter"
          >
            →
          </button>
        </div>
      </div>
    </div>

    <!-- Timeline grid -->
    <div class="flex-1 overflow-auto p-6">
      <div v-if="loading" class="flex items-center justify-center h-32 text-gray-400">
        Loading roadmap…
      </div>
      <div v-else>
        <!-- Week header -->
        <div class="relative h-8 mb-2 ml-40">
          <div
            v-for="week in weeks"
            :key="week.toISOString()"
            class="absolute text-xs text-gray-400"
            :style="{
              left: `${(differenceInDays(week, currentQuarterStart) / totalDays) * 100}%`,
            }"
          >
            {{ format(week, 'MMM d') }}
          </div>
        </div>

        <!-- Sprint rows -->
        <div class="space-y-3">
          <div
            v-for="sprint in filteredSprints"
            :key="sprint.id"
            class="flex items-center gap-3"
          >
            <!-- Sprint name -->
            <div class="w-40 flex-shrink-0 text-sm font-medium text-gray-700 dark:text-gray-300 truncate">
              {{ sprint.name }}
            </div>

            <!-- Timeline bar -->
            <div class="relative flex-1 h-10 bg-gray-100 dark:bg-gray-800 rounded-lg overflow-hidden">
              <div
                class="absolute top-1 bottom-1 rounded-md flex items-center px-2 text-xs text-white font-medium overflow-hidden"
                :class="sprintColor(sprint)"
                :style="sprintStyle(sprint)"
              >
                <!-- Epic chips -->
                <div class="flex gap-1 overflow-hidden">
                  <span
                    v-for="epic in getEpicsForSprint(sprint.id)"
                    :key="epic.id"
                    class="bg-white/20 rounded px-1 truncate"
                  >
                    {{ epic.title }}
                  </span>
                  <span v-if="!getEpicsForSprint(sprint.id).length" class="truncate">
                    {{ sprint.name }}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <div
            v-if="filteredSprints.length === 0"
            class="text-center text-gray-400 py-12"
          >
            No sprints found for this quarter.
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
