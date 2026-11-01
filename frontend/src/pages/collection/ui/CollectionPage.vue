<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Heart, Users } from 'lucide-vue-next'
import { BaseButton } from '@/shared/ui/button'
const route = useRoute()
const router = useRouter()
const favorites = computed(() => route.name === 'favorites')
</script>
<template>
  <div class="workspace-page">
    <header class="page-heading">
      <h1 class="title-1">{{ favorites ? 'Избранное' : 'Сообщество' }}</h1>
      <p class="text-1 muted">
        {{ favorites ? 'Сохранённые материалы для вашего обучения' : 'Учись вместе с другими' }}
      </p>
    </header>
    <section class="surface empty-state">
      <component :is="favorites ? Heart : Users" :size="56" />
      <h2 class="title-4">
        {{ favorites ? 'Избранное скоро появится' : 'Публичные материалы скоро появятся' }}
      </h2>
      <p class="text-3 muted">
        {{
          favorites
            ? 'Сохранение материалов в избранное пока недоступно.'
            : 'Публикация материалов и просмотр работ других студентов пока недоступны.'
        }}
      </p>
      <BaseButton @click="router.push('/materials')">Перейти к моим материалам</BaseButton>
    </section>
  </div>
</template>
