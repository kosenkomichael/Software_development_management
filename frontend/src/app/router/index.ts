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
          path: 'forgot-password',
          component: () => import('@/pages/password-recovery/ui/PasswordRecoveryPage.vue'),
          meta: { title: 'Восстановление пароля' },
        },
        {
          path: 'reset-password',
          component: () => import('@/pages/password-recovery/ui/PasswordRecoveryPage.vue'),
          props: { reset: true },
          meta: { title: 'Новый пароль' },
        },
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
          path: 'community/materials/:materialId', name: 'public-material',
          component: () => import('@/pages/public-material/ui/PublicMaterialPage.vue'),
          meta: { requiresAuth: true, title: 'Учебный материал' },
        },
        {
          path: 'community/quizzes/:quizId', name: 'public-quiz',
          component: () => import('@/pages/public-quiz/ui/PublicQuizPage.vue'),
          meta: { requiresAuth: true, title: 'Публичный тест' },
        },
        {
          path: 'community/attempts/:attemptId', name: 'public-attempt',
          component: () => import('@/pages/public-quiz/ui/PublicQuizPage.vue'),
          meta: { requiresAuth: true, title: 'Сохранённая попытка' },
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
          component: () => import('@/pages/materials').then((module) => module.MaterialsPage),
          props: { favoritesOnly: true },
          meta: { requiresAuth: true, title: 'Избранное' },
        },
      ],
    },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
})

router.onError((error, to) => {
  if (!/Failed to fetch dynamically imported module|Importing a module script failed|error loading dynamically imported module|Unable to preload CSS/i.test(String(error))) return
  // A tab opened before deployment can still reference the previous build's chunks.
  // Reload the destination once; avoid a loop if the server is actually unavailable.
  try {
    const key = `studyai.navigation-reload:${to.path}`
    const previous = Number(sessionStorage.getItem(key))
    if (Date.now() - previous < 30000) return
    sessionStorage.setItem(key, String(Date.now()))
  } catch {
    return
  }
  window.location.assign(to.fullPath)
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
