<script setup lang="ts">
import { computed } from 'vue'
import { useTaskStore } from '@/stores/tasks'
import { useWorkspaceStore } from '@/stores/workspace'
import KanbanColumn from './KanbanColumn.vue'
import { KANBAN_COLUMNS } from '@/lib/constants'

const taskStore = useTaskStore()
const workspaceStore = useWorkspaceStore()

const workspaceId = computed(() => workspaceStore.currentWorkspaceId ?? '')
</script>

<template>
  <div class="flex gap-4 h-full overflow-x-auto px-6 py-4">
    <KanbanColumn
      v-for="status in KANBAN_COLUMNS"
      :key="status"
      :status="status"
      :tasks="taskStore.tasksByStatus[status]"
      :workspace-id="workspaceId"
    />
  </div>
</template>
