import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import Avatar from '@/components/shared/Avatar.vue'

describe('Avatar', () => {
  it('renders image when avatarUrl is provided', () => {
    const wrapper = mount(Avatar, {
      props: {
        avatarUrl: 'https://example.com/avatar.jpg',
        displayName: 'Alice Smith',
        userId: 'user-1',
      },
    })
    expect(wrapper.find('img').exists()).toBe(true)
    expect(wrapper.find('img').attributes('src')).toBe('https://example.com/avatar.jpg')
  })

  it('renders initials fallback when no avatar URL', () => {
    const wrapper = mount(Avatar, {
      props: {
        avatarUrl: null,
        displayName: 'Bob Jones',
        userId: 'user-2',
      },
    })
    expect(wrapper.find('img').exists()).toBe(false)
    expect(wrapper.text()).toContain('BJ')
  })

  it('renders single initial for single name', () => {
    const wrapper = mount(Avatar, {
      props: {
        avatarUrl: null,
        displayName: 'Alice',
        userId: 'user-3',
      },
    })
    expect(wrapper.text()).toContain('A')
  })

  it('applies sm size classes', () => {
    const wrapper = mount(Avatar, {
      props: { userId: 'user-1', size: 'sm' },
    })
    expect(wrapper.html()).toMatch(/w-6|h-6|w-7|h-7|w-8|h-8/)
  })

  it('applies lg size classes', () => {
    const wrapper = mount(Avatar, {
      props: { userId: 'user-1', size: 'lg' },
    })
    expect(wrapper.html()).toMatch(/w-10|h-10|w-12|h-12/)
  })
})
