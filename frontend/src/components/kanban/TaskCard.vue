<script setup lang="ts">
import { computed } from 'vue'
import { format, isPast } from 'date-fns'
import Avatar from '@/components/shared/Avatar.vue'
import { TASK_TYPE_ICONS, TASK_PRIORITY_COLORS } from '@/lib/constants'
import type { Task } from '@/types'

const props = defineProps<{ task: Task }>()
const emit = defineEmits<{ click: [task: Task] }>()

const priorityBorderColors: Record<string, string> = {
  low: 'border-l-gray-300',
  medium: 'border-l-blue-400',
  high: 'border-l-orange-400',
  critical: 'border-l-red-500',
}

const isOverdue = computed(() =>
  props.task.due_date &&
  isPast(new Date(props.task.due_date)) &&
  props.task.status !== 'done'
)

function formatDue(date: string) {
  return format(new Date(date), 'MMM d')
}
</script>

<template>
  <div
    class="bg-white dark:bg-surface-dark-elevated rounded-lg shadow-sm p-3 border-l-4 cursor-pointer hover:shadow-md transition-shadow select-none"
    :class="priorityBorderColors[task.priority]"
    @click="emit('click', task)"
  >
    <!-- Type icon + title -->
    <div class="flex items-start gap-1.5">
      <span class="text-sm flex-shrink-0 mt-0.5">{{ TASK_TYPE_ICONS[task.type] }}</span>
      <p class="text-sm font-medium text-gray-800 dark:text-gray-200 leading-snug line-clamp-2">
        {{ task.title }}
      </p>
    </div>

    <!-- Labels -->
    <div v-if="task.labels.length" class="flex flex-wrap gap-1 mt-2">
      <span
        v-for="label in task.labels.slice(0, 3)"
        :key="label"
        class="text-xs px-1.5 py-0.5 bg-brand-50 dark:bg-brand-900/20 text-brand-600 dark:text-brand-300 rounded"
      >
        {{ label }}
      </span>
    </div>

    <!-- Bottom row -->
    <div class="flex items-center justify-between mt-2.5">
      <!-- Assignee avatars -->
      <div class="flex -space-x-1.5">
        <Avatar
          v-for="assignee in (task.assignees ?? []).slice(0, 3)"
          :key="assignee.id"
          :src="assignee.avatar_url"
          :name="assignee.display_name"
          size="xs"
          class="ring-1 ring-white dark:ring-surface-dark"
        />
        <div
          v-if="(task.assignees?.length ?? 0) > 3"
          class="w-6 h-6 rounded-full bg-gray-200 dark:bg-gray-700 text-xs flex items-center justify-center text-gray-600 dark:text-gray-400 ring-1 ring-white dark:ring-surface-dark"
        >
          +{{ (task.assignees?.length ?? 0) - 3 }}
        </div>
      </div>

      <div class="flex items-center gap-2">
        <!-- Story points -->
        <span
          v-if="task.story_points !== null"
          class="text-xs bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400 rounded px-1.5 py-0.5 font-mono"
        >
          {{ task.story_points }}
        </span>

        <!-- GitHub PR icon -->
        <span v-if="task.github_pr_urls.length" class="text-xs text-gray-400" title="Has open PRs">
          🔗
        </span>

        <!-- Due date -->
        <span
          v-if="task.due_date"
          class="text-xs"
          :class="isOverdue ? 'text-red-500 font-medium' : 'text-gray-400'"
        >
          {{ formatDue(task.due_date) }}
        </span>
      </div>
    </div>
  </div>
</template>
