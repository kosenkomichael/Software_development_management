<script setup lang="ts">
import { useRoute } from 'vue-router'
import { QuizPanel } from '@/features/take-quiz'
const route = useRoute()
</script>
<template>
  <div class="workspace-page">
    <RouterLink class="text-link text-3" to="/community">Вернуться в сообщество</RouterLink>
    <h1 class="title-3">{{ route.params.attemptId ? 'Сохранённая попытка' : 'Публичный тест' }}</h1>
    <QuizPanel :key="route.fullPath" material-id="public" :public-quiz-id="route.params.quizId ? String(route.params.quizId) : undefined" :saved-public-attempt-id="route.params.attemptId ? String(route.params.attemptId) : undefined" />
  </div>
</template>
