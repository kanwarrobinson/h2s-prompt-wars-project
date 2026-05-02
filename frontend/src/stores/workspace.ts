import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/lib/api'
import type { Workspace, WorkspaceMember } from '@/types'

export const useWorkspaceStore = defineStore('workspace', () => {
  const workspaces = ref<Workspace[]>([])
  const currentWorkspace = ref<Workspace | null>(null)
  const members = ref<WorkspaceMember[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  const currentWorkspaceId = computed(() => currentWorkspace.value?.id ?? null)
  const isAdmin = computed(() => {
    const uid = currentWorkspace.value?.owner_id
    return !!uid
  })

  async function fetchWorkspaces(): Promise<void> {
    loading.value = true
    try {
      const { data } = await api.get('/api/v1/workspaces')
      workspaces.value = data
      if (data.length && !currentWorkspace.value) {
        currentWorkspace.value = data[0]
      }
    } finally {
      loading.value = false
    }
  }

  async function selectWorkspace(id: string): Promise<void> {
    const ws = workspaces.value.find((w) => w.id === id)
    if (ws) {
      currentWorkspace.value = ws
    } else {
      const { data } = await api.get(`/api/v1/workspaces/${id}`)
      currentWorkspace.value = data
    }
  }

  async function createWorkspace(name: string, slug: string): Promise<Workspace> {
    const { data } = await api.post('/api/v1/workspaces', { name, slug })
    workspaces.value.push(data)
    return data
  }

  async function fetchMembers(): Promise<void> {
    if (!currentWorkspaceId.value) return
    const { data } = await api.get(`/api/v1/workspaces/${currentWorkspaceId.value}`)
    members.value = data.members ?? []
  }

  async function inviteMember(email: string, role: string): Promise<void> {
    await api.post(`/api/v1/workspaces/${currentWorkspaceId.value}/members`, { email, role })
    await fetchMembers()
  }

  async function removeMember(userId: string): Promise<void> {
    await api.delete(`/api/v1/workspaces/${currentWorkspaceId.value}/members/${userId}`)
    members.value = members.value.filter((m) => m.user_id !== userId)
  }

  return {
    workspaces,
    currentWorkspace,
    members,
    loading,
    error,
    currentWorkspaceId,
    isAdmin,
    fetchWorkspaces,
    selectWorkspace,
    createWorkspace,
    fetchMembers,
    inviteMember,
    removeMember,
  }
})
