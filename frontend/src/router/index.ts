import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  { path: '/', redirect: '/dashboard' },
  {
    path: '/login',
    component: () => import('@/views/Login.vue'),
    meta: { public: true },
  },
  {
    path: '/dashboard',
    component: () => import('@/views/Dashboard.vue'),
  },
  {
    path: '/board',
    component: () => import('@/views/SprintBoard.vue'),
  },
  {
    path: '/channels/:channelId',
    component: () => import('@/views/Channel.vue'),
  },
  {
    path: '/dm/:userId',
    component: () => import('@/views/DirectMessage.vue'),
  },
  {
    path: '/roadmap',
    component: () => import('@/views/Roadmap.vue'),
  },
  {
    path: '/settings',
    component: () => import('@/views/Settings.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to) => {
  const authStore = useAuthStore()

  if (authStore.loading) {
    await new Promise<void>((resolve) => {
      const unwatch = authStore.$subscribe(() => {
        if (!authStore.loading) {
          unwatch()
          resolve()
        }
      })
    })
  }

  if (!to.meta.public && !authStore.isAuthenticated) {
    return '/login'
  }

  if (to.path === '/login' && authStore.isAuthenticated) {
    return '/dashboard'
  }
})

export default router
