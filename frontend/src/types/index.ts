export type TaskStatus = 'backlog' | 'todo' | 'in_progress' | 'review' | 'done'
export type TaskType = 'task' | 'bug' | 'story' | 'epic'
export type TaskPriority = 'low' | 'medium' | 'high' | 'critical'
export type WorkspacePlan = 'free' | 'pro' | 'enterprise'
export type MemberRole = 'admin' | 'member' | 'guest'
export type SprintStatus = 'planned' | 'active' | 'completed'
export type ChannelType = 'public' | 'private' | 'dm'
export type PresenceStatus = 'online' | 'away' | 'offline'
export type DigestFreq = 'none' | 'daily' | 'weekly'

export interface User {
  id: string
  firebase_uid: string
  email: string
  display_name: string
  avatar_url: string | null
  workspace_ids: string[]
  notification_prefs: NotificationPrefs
  created_at: string
}

export interface NotificationPrefs {
  email_digest: DigestFreq
  push_enabled: boolean
  mention_only: boolean
}

export interface WorkspaceMember {
  user_id: string
  role: MemberRole
  joined_at: string
  user?: User
}

export interface WorkspaceSettings {
  allowed_domains: string[]
  sso_enabled: boolean
  github_org: string | null
}

export interface Workspace {
  id: string
  name: string
  slug: string
  plan: WorkspacePlan
  owner_id: string
  members: WorkspaceMember[]
  settings: WorkspaceSettings
  created_at: string
  updated_at: string
}

export interface TaskComment {
  id: string
  author_id: string
  body: string
  created_at: string
  author?: User
}

export interface TaskAttachment {
  name: string
  gcs_path: string
  size: number
  url?: string
}

export interface Task {
  id: string
  workspace_id: string
  project_id: string
  sprint_id: string | null
  title: string
  description: string
  type: TaskType
  status: TaskStatus
  priority: TaskPriority
  assignee_ids: string[]
  reporter_id: string
  labels: string[]
  story_points: number | null
  due_date: string | null
  github_pr_urls: string[]
  comments: TaskComment[]
  attachments: TaskAttachment[]
  created_at: string
  updated_at: string
  assignees?: User[]
  reporter?: User
}

export interface Sprint {
  id: string
  workspace_id: string
  project_id: string
  name: string
  goal: string
  start_date: string
  end_date: string
  status: SprintStatus
  velocity: number
}

export interface Project {
  id: string
  workspace_id: string
  name: string
  color: string
  github_repo: string | null
  created_at: string
}

export interface MessageReaction {
  emoji: string
  user_ids: string[]
}

export interface Message {
  id: string
  workspace_id: string
  channel_id: string
  author_id: string
  body: string
  thread_id: string | null
  mentions: string[]
  attachments: string[]
  reactions: MessageReaction[]
  edited: boolean
  created_at: string
  author?: User
  reply_count?: number
}

export interface Channel {
  id: string
  workspace_id: string
  name: string
  type: ChannelType
  member_ids: string[]
  topic: string
  created_at: string
  unread_count?: number
}

export interface Notification {
  id: string
  type: string
  title: string
  body: string
  read: boolean
  created_at: string
}

export interface PaginatedResponse<T> {
  items: T[]
  cursor: string | null
  total: number
}

export interface ApiError {
  detail: string
  status: number
}
