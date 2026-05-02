<script setup lang="ts">
import { computed } from 'vue'
import { useTaskStore } from '@/stores/tasks'
import { useWorkspaceStore } from '@/stores/workspace'
import Avatar from '@/components/shared/Avatar.vue'
import { TASK_PRIORITY_LABELS } from '@/lib/constants'
import type { TaskPriority } from '@/types'

const taskStore = useTaskStore()
const workspaceStore = useWorkspaceStore()

const priorities: TaskPriority[] = ['low', 'medium', 'high', 'critical']

const priorityColors: Record<TaskPriority, string> = {
  low: 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400',
  medium: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  high: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
  critical: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
}

const hasActiveFilters = computed(
  () =>
    !!taskStore.filters.assignee ||
    !!taskStore.filters.priority ||
    !!taskStore.filters.label
)

function toggleAssigneeFilter(userId: string) {
  taskStore.filters.assignee =
    taskStore.filters.assignee === userId ? '' : userId
}

function togglePriorityFilter(priority: TaskPriority) {
  taskStore.filters.priority =
    taskStore.filters.priority === priority ? '' : priority
}

function clearFilters() {
  taskStore.filters.assignee = ''
  taskStore.filters.priority = ''
  taskStore.filters.label = ''
}
</script>

<template>
  <div class="flex flex-wrap items-center gap-3">
    <!-- Assignee filters (member avatars as toggles) -->
    <div class="flex items-center gap-1">
      <button
        v-for="member in workspaceStore.members"
        :key="member.user_id"
        :title="member.user?.display_name ?? member.user_id"
        class="rounded-full transition-all"
        :class="
          taskStore.filters.assignee === member.user_id
            ? 'ring-2 ring-brand-500 ring-offset-1'
            : 'opacity-60 hover:opacity-100'
        "
        @click="toggleAssigneeFilter(member.user_id)"
      >
        <Avatar
          :src="member.user?.avatar_url"
          :name="member.user?.display_name ?? member.user_id"
          size="xs"
        />
      </button>
    </div>

    <!-- Priority filters -->
    <div class="flex items-center gap-1">
      <button
        v-for="priority in priorities"
        :key="priority"
        class="px-2.5 py-1 rounded-full text-xs font-medium transition-all"
        :class="[
          priorityColors[priority],
          taskStore.filters.priority === priority ? 'ring-2 ring-offset-1 ring-brand-500' : 'opacity-70 hover:opacity-100',
        ]"
        @click="togglePriorityFilter(priority)"
      >
        {{ TASK_PRIORITY_LABELS[priority] }}
      </button>
    </div>

    <!-- Label filter -->
    <input
      v-model="taskStore.filters.label"
      type="text"
      placeholder="Filter by label…"
      class="text-xs border border-gray-200 dark:border-gray-600 rounded-lg px-2.5 py-1 bg-white dark:bg-surface-dark text-gray-700 dark:text-gray-300 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-brand-500"
    />

    <!-- Clear filters -->
    <button
      v-if="hasActiveFilters"
      class="text-xs text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
      @click="clearFilters"
    >
      Clear filters ✕
    </button>
  </div>
</template>
