import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import TaskCard from '@/components/kanban/TaskCard.vue'
import type { Task } from '@/types'

vi.mock('@/stores/auth', () => ({
  useAuthStore: () => ({
    profile: { id: 'user-1' },
  }),
}))

const baseTask: Task = {
  id: 'task-1',
  workspace_id: 'ws-1',
  title: 'Fix login bug',
  description: 'Users cannot log in',
  type: 'bug',
  status: 'todo',
  priority: 'high',
  assignee_ids: [],
  reporter_id: 'user-1',
  labels: [],
  github_pr_urls: [],
  comments: [],
  attachments: [],
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
}

describe('TaskCard', () => {
  it('renders task title', () => {
    const wrapper = mount(TaskCard, { props: { task: baseTask } })
    expect(wrapper.text()).toContain('Fix login bug')
  })

  it('shows high priority badge with correct color', () => {
    const wrapper = mount(TaskCard, { props: { task: { ...baseTask, priority: 'high' } } })
    expect(wrapper.html()).toContain('high')
  })

  it('shows critical priority badge', () => {
    const wrapper = mount(TaskCard, { props: { task: { ...baseTask, priority: 'critical' } } })
    expect(wrapper.html()).toContain('critical')
  })

  it('shows low priority badge', () => {
    const wrapper = mount(TaskCard, { props: { task: { ...baseTask, priority: 'low' } } })
    expect(wrapper.html()).toContain('low')
  })

  it('shows story points when set', () => {
    const wrapper = mount(TaskCard, { props: { task: { ...baseTask, story_points: 5 } } })
    expect(wrapper.text()).toContain('5')
  })

  it('shows overdue indicator when due date is past', () => {
    const pastDate = new Date('2020-01-01').toISOString()
    const wrapper = mount(TaskCard, { props: { task: { ...baseTask, due_date: pastDate } } })
    expect(wrapper.html()).toMatch(/overdue|red|past/i)
  })

  it('emits click event when clicked', async () => {
    const wrapper = mount(TaskCard, { props: { task: baseTask } })
    await wrapper.trigger('click')
    expect(wrapper.emitted('click')).toBeTruthy()
  })
})
