<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { format, isPast } from 'date-fns'
import { useTaskStore } from '@/stores/tasks'
import { useWorkspaceStore } from '@/stores/workspace'
import { useAuthStore } from '@/stores/auth'
import Avatar from '@/components/shared/Avatar.vue'
import {
  TASK_STATUS_LABELS,
  TASK_STATUS_COLORS,
  TASK_PRIORITY_LABELS,
  TASK_PRIORITY_COLORS,
  TASK_TYPE_ICONS,
} from '@/lib/constants'
import type { Task, TaskStatus, TaskPriority, TaskType, WorkspaceMember } from '@/types'
import api from '@/lib/api'

const props = defineProps<{
  task: Task
  workspaceId: string
}>()

const emit = defineEmits<{
  close: []
  updated: []
}>()

const taskStore = useTaskStore()
const workspaceStore = useWorkspaceStore()
const authStore = useAuthStore()

const isEditing = ref(false)
const editTitle = ref(props.task.title)
const editDescription = ref(props.task.description)
const previewMode = ref(false)
const saving = ref(false)
const deleting = ref(false)
const commentBody = ref('')
const commentSending = ref(false)
const members = ref<WorkspaceMember[]>([])

const statuses: TaskStatus[] = ['backlog', 'todo', 'in_progress', 'review', 'done']
const priorities: TaskPriority[] = ['low', 'medium', 'high', 'critical']
const types: TaskType[] = ['task', 'bug', 'story', 'epic']

const isOverdue = computed(
  () => props.task.due_date && isPast(new Date(props.task.due_date)) && props.task.status !== 'done'
)

function formatDate(dateStr: string) {
  return format(new Date(dateStr), 'MMM d, yyyy')
}

async function saveField(field: string, value: unknown) {
  saving.value = true
  try {
    await taskStore.updateTask(props.workspaceId, props.task.id, { [field]: value } as Partial<Task>)
  } finally {
    saving.value = false
  }
}

async function saveTitle() {
  if (!editTitle.value.trim()) return
  await saveField('title', editTitle.value.trim())
  isEditing.value = false
}

async function saveDescription() {
  await saveField('description', editDescription.value)
  previewMode.value = true
}

async function submitComment() {
  if (!commentBody.value.trim()) return
  commentSending.value = true
  try {
    await taskStore.addComment(props.workspaceId, props.task.id, commentBody.value.trim())
    commentBody.value = ''
  } finally {
    commentSending.value = false
  }
}

async function deleteTask() {
  if (!confirm('Delete this task? This cannot be undone.')) return
  deleting.value = true
  try {
    await taskStore.deleteTask(props.workspaceId, props.task.id)
    emit('updated')
  } finally {
    deleting.value = false
  }
}

async function toggleAssignee(userId: string) {
  const ids = props.task.assignee_ids.includes(userId)
    ? props.task.assignee_ids.filter((id) => id !== userId)
    : [...props.task.assignee_ids, userId]
  await saveField('assignee_ids', ids)
}

onMounted(async () => {
  members.value = workspaceStore.members.length
    ? workspaceStore.members
    : await workspaceStore.fetchMembers().then(() => workspaceStore.members)
})
</script>

<template>
  <div class="p-6">
    <!-- Header -->
    <div class="flex items-start justify-between gap-4 mb-4">
      <div class="flex-1 min-w-0">
        <!-- Editable title -->
        <div v-if="isEditing">
          <input
            v-model="editTitle"
            type="text"
            class="w-full text-xl font-bold bg-transparent border-b-2 border-brand-500 text-gray-900 dark:text-white focus:outline-none pb-1"
            autofocus
            @keydown.enter="saveTitle"
            @keydown.escape="isEditing = false"
          />
          <div class="flex gap-2 mt-2">
            <button
              class="text-xs px-3 py-1 bg-brand-500 text-white rounded-lg"
              @click="saveTitle"
            >
              Save
            </button>
            <button
              class="text-xs px-3 py-1 text-gray-500 hover:text-gray-700"
              @click="isEditing = false"
            >
              Cancel
            </button>
          </div>
        </div>
        <h1
          v-else
          class="text-xl font-bold text-gray-900 dark:text-white cursor-pointer hover:text-brand-500 transition-colors"
          @click="isEditing = true"
        >
          {{ task.title }}
        </h1>
      </div>
      <button
        class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 flex-shrink-0"
        @click="emit('close')"
      >
        ✕
      </button>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <!-- Left: Description + Comments -->
      <div class="md:col-span-2 space-y-5">
        <!-- Description -->
        <div>
          <p class="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">Description</p>
          <div v-if="previewMode && task.description">
            <div
              class="prose prose-sm dark:prose-invert text-gray-700 dark:text-gray-300 cursor-pointer"
              @click="previewMode = false"
            >
              {{ task.description }}
            </div>
          </div>
          <div v-else>
            <textarea
              v-model="editDescription"
              rows="4"
              placeholder="Add a description…"
              class="w-full text-sm border border-gray-200 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200 focus:outline-none focus:ring-2 focus:ring-brand-500 resize-none"
            />
            <div class="flex gap-2 mt-1">
              <button
                class="text-xs px-3 py-1 bg-brand-500 text-white rounded-lg hover:bg-brand-600"
                @click="saveDescription"
              >
                Save
              </button>
              <button
                v-if="task.description"
                class="text-xs px-3 py-1 text-gray-500 hover:text-gray-700"
                @click="previewMode = true"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>

        <!-- Comments -->
        <div>
          <p class="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-3">
            Comments ({{ task.comments.length }})
          </p>

          <div class="space-y-3 mb-4">
            <div
              v-for="comment in task.comments"
              :key="comment.id"
              class="flex gap-2"
            >
              <Avatar
                :name="comment.author?.display_name ?? 'User'"
                :src="comment.author?.avatar_url"
                size="sm"
                class="flex-shrink-0"
              />
              <div class="flex-1 bg-gray-50 dark:bg-gray-800 rounded-lg px-3 py-2">
                <div class="flex items-baseline gap-2 mb-1">
                  <span class="text-xs font-semibold text-gray-700 dark:text-gray-300">
                    {{ comment.author?.display_name ?? 'Unknown' }}
                  </span>
                  <span class="text-xs text-gray-400">{{ formatDate(comment.created_at) }}</span>
                </div>
                <p class="text-sm text-gray-700 dark:text-gray-300">{{ comment.body }}</p>
              </div>
            </div>
          </div>

          <!-- Add comment -->
          <div class="flex gap-2">
            <Avatar
              :src="authStore.avatarUrl"
              :name="authStore.displayName || 'Me'"
              size="sm"
              class="flex-shrink-0"
            />
            <div class="flex-1">
              <textarea
                v-model="commentBody"
                rows="2"
                placeholder="Add a comment…"
                class="w-full text-sm border border-gray-200 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200 focus:outline-none focus:ring-2 focus:ring-brand-500 resize-none"
              />
              <button
                :disabled="!commentBody.trim() || commentSending"
                class="mt-1 text-xs px-3 py-1.5 bg-brand-500 text-white rounded-lg hover:bg-brand-600 disabled:opacity-50 transition-colors"
                @click="submitComment"
              >
                {{ commentSending ? 'Sending…' : 'Comment' }}
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Right: Metadata -->
      <div class="space-y-4">
        <!-- Status -->
        <div>
          <p class="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1">Status</p>
          <select
            :value="task.status"
            class="w-full text-sm border border-gray-200 dark:border-gray-600 rounded-lg px-2 py-1.5 bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
            @change="saveField('status', ($event.target as HTMLSelectElement).value)"
          >
            <option v-for="s in statuses" :key="s" :value="s">
              {{ TASK_STATUS_LABELS[s] }}
            </option>
          </select>
        </div>

        <!-- Priority -->
        <div>
          <p class="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1">Priority</p>
          <select
            :value="task.priority"
            class="w-full text-sm border border-gray-200 dark:border-gray-600 rounded-lg px-2 py-1.5 bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
            @change="saveField('priority', ($event.target as HTMLSelectElement).value)"
          >
            <option v-for="p in priorities" :key="p" :value="p">
              {{ TASK_PRIORITY_LABELS[p] }}
            </option>
          </select>
        </div>

        <!-- Type -->
        <div>
          <p class="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1">Type</p>
          <select
            :value="task.type"
            class="w-full text-sm border border-gray-200 dark:border-gray-600 rounded-lg px-2 py-1.5 bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
            @change="saveField('type', ($event.target as HTMLSelectElement).value)"
          >
            <option v-for="t in types" :key="t" :value="t">
              {{ TASK_TYPE_ICONS[t] }} {{ t }}
            </option>
          </select>
        </div>

        <!-- Assignees -->
        <div>
          <p class="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1">Assignees</p>
          <div class="space-y-1">
            <label
              v-for="member in members"
              :key="member.user_id"
              class="flex items-center gap-2 cursor-pointer p-1 rounded hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
            >
              <input
                type="checkbox"
                :checked="task.assignee_ids.includes(member.user_id)"
                class="accent-brand-500"
                @change="toggleAssignee(member.user_id)"
              />
              <Avatar
                :name="member.user?.display_name ?? member.user_id"
                :src="member.user?.avatar_url"
                size="xs"
              />
              <span class="text-xs text-gray-700 dark:text-gray-300">
                {{ member.user?.display_name ?? member.user_id }}
              </span>
            </label>
          </div>
        </div>

        <!-- Story points -->
        <div>
          <p class="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1">Story Points</p>
          <input
            :value="task.story_points ?? ''"
            type="number"
            min="0"
            max="100"
            class="w-full text-sm border border-gray-200 dark:border-gray-600 rounded-lg px-2 py-1.5 bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
            @change="saveField('story_points', Number(($event.target as HTMLInputElement).value) || null)"
          />
        </div>

        <!-- Due date -->
        <div>
          <p class="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1">Due Date</p>
          <input
            :value="task.due_date?.slice(0, 10) ?? ''"
            type="date"
            class="w-full text-sm border border-gray-200 dark:border-gray-600 rounded-lg px-2 py-1.5 bg-white dark:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-brand-500"
            :class="isOverdue ? 'text-red-500' : 'text-gray-800 dark:text-gray-200'"
            @change="saveField('due_date', ($event.target as HTMLInputElement).value || null)"
          />
        </div>

        <!-- Labels -->
        <div>
          <p class="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1">Labels</p>
          <div class="flex flex-wrap gap-1 mb-1">
            <span
              v-for="label in task.labels"
              :key="label"
              class="text-xs px-2 py-0.5 bg-brand-50 dark:bg-brand-900/20 text-brand-600 dark:text-brand-300 rounded-full"
            >
              {{ label }}
            </span>
          </div>
        </div>

        <!-- GitHub PRs -->
        <div v-if="task.github_pr_urls.length">
          <p class="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1">GitHub PRs</p>
          <div class="space-y-1">
            <a
              v-for="url in task.github_pr_urls"
              :key="url"
              :href="url"
              target="_blank"
              rel="noopener noreferrer"
              class="flex items-center gap-1 text-xs text-brand-500 hover:underline"
            >
              🔗 {{ url.split('/').slice(-2).join('#') }}
            </a>
          </div>
        </div>

        <!-- Delete (admin only) -->
        <div v-if="workspaceStore.isAdmin" class="pt-2 border-t border-gray-200 dark:border-gray-700">
          <button
            :disabled="deleting"
            class="w-full text-xs text-red-500 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg py-1.5 transition-colors disabled:opacity-50"
            @click="deleteTask"
          >
            {{ deleting ? 'Deleting…' : '🗑 Delete Task' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
