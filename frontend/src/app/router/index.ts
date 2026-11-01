import { createRouter, createWebHistory } from 'vue-router'

import MainLayout from '@/app/layouts/MainLayout.vue'
import WorkspaceLayout from '@/app/layouts/WorkspaceLayout.vue'
import { MainPage } from '@/pages/main'
import { useSessionStore } from '@/entities/session'
import { useAuthModalStore } from '@/features/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  scrollBehavior(to, from, saved) {
    if (saved) return saved
    if (to.hash) return { el: to.hash, behavior: 'smooth' }
    if (to.path === from.path) return false
    return { top: 0 }
  },

  routes: [
    {
      path: '/',
      component: MainLayout,
      children: [
        {
          path: '',
          name: 'main',
          component: MainPage,
        },
      ],
    },
    {
      path: '/',
      component: WorkspaceLayout,
      children: [
        {
          path: 'account',
          name: 'account',
          component: () => import('@/pages/account').then((module) => module.AccountPage),
          meta: { requiresAuth: true, title: 'Личный кабинет' },
        },
        {
          path: 'materials',
          name: 'materials',
          component: () => import('@/pages/materials').then((module) => module.MaterialsPage),
          meta: { requiresAuth: true, title: 'Мои материалы' },
        },
        {
          path: 'materials/new',
          name: 'create-material',
          component: () =>
            import('@/pages/create-material').then((module) => module.CreateMaterialPage),
          meta: { requiresAuth: true, title: 'Создать материал' },
        },
        {
          path: 'materials/new/:id',
          name: 'material-processing',
          component: () => import('@/pages/material').then((module) => module.MaterialPage),
          meta: { requiresAuth: true, creatingMaterial: true, title: 'Создать материал' },
        },
        {
          path: 'materials/:id',
          name: 'material',
          component: () =>
            import('@/pages/material-detail').then((module) => module.MaterialDetailPage),
          meta: { requiresAuth: true, materialDetail: true, title: 'Материал' },
        },
        {
          path: 'demo',
          name: 'demo',
          component: () => import('@/pages/material').then((module) => module.MaterialPage),
          meta: { publicPreview: true, title: 'Пример результата' },
        },
        {
          path: 'community',
          name: 'community',
          component: () => import('@/pages/collection').then((module) => module.CollectionPage),
          meta: { requiresAuth: true, title: 'Сообщество' },
        },
        {
          path: 'favorites',
          name: 'favorites',
          component: () => import('@/pages/collection').then((module) => module.CollectionPage),
          meta: { requiresAuth: true, title: 'Избранное' },
        },
      ],
    },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
})

router.beforeEach(async (to) => {
  if (!to.meta.requiresAuth) return
  const session = useSessionStore()
  if (session.isInitializing) await session.initialize()
  if (!session.isAuthenticated) {
    const auth = useAuthModalStore()
    auth.redirectTo = to.fullPath
    auth.open('login')
    return '/'
  }
})
router.afterEach((to) => {
  document.title = to.meta.title
    ? `${String(to.meta.title)} — StudyAI`
    : 'StudyAI — конспекты и тесты из лекций'
})

export default router
