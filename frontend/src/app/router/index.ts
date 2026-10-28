import { createRouter, createWebHistory } from 'vue-router'

import MainLayout from '@/app/layouts/MainLayout.vue'
import { MainPage } from '@/pages/main'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),

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
  ],
})

export default router
