<script setup lang="ts">
import { onBeforeUnmount, ref, watch } from 'vue'
import { createPublicQuizApi, formatTrainingTime } from '@/entities/material'
import { useSessionStore } from '@/entities/session'
import { BaseButton } from '@/shared/ui/button'
const props = defineProps<{ quizId: string; revision: number }>()
const api = createPublicQuizApi(useSessionStore().request)
const data = ref<Awaited<ReturnType<typeof api.leaderboard>> | null>(null)
const loading = ref(false)
const error = ref('')
let controller = new AbortController()
async function load() {
  controller.abort(); controller = new AbortController()
  const signal = controller.signal
  loading.value = true; error.value = ''
  try { const response = await api.leaderboard(props.quizId, signal); if (!signal.aborted) data.value = response }
  catch (reason) { if (!signal.aborted) error.value = reason instanceof Error ? reason.message : 'Не удалось загрузить рейтинг.' }
  finally { if (!signal.aborted) loading.value = false }
}
watch(() => `${props.quizId}:${props.revision}`, () => void load(), { immediate: true })
onBeforeUnmount(() => controller.abort())
</script>
<template>
  <section class="quiz-leaderboard">
    <div class="section-heading"><h3 class="title-4">Рейтинг тренировок</h3><BaseButton variant="transparent" :disabled="loading" @click="load">Обновить</BaseButton></div>
    <p class="text-3 muted">По одной лучшей попытке каждого участника. Сначала процент, затем время. Повторять тест можно сколько угодно.</p>
    <p v-if="error" class="text-3 danger" role="alert">{{ error }}</p>
    <p v-if="loading" class="text-3 muted" role="status">Загружаем рейтинг…</p>
    <p v-else-if="data && !data.participants" class="text-3 muted">Пока нет завершённых тренировок на время. Станьте первым участником.</p>
    <template v-if="data?.participants">
      <p class="text-3">Участников: {{ data.participants }}<template v-if="data.my_entry"> · Ваше место: {{ data.my_entry.rank }}</template></p>
      <div class="quiz-leaderboard__scroll"><table class="text-3"><thead><tr><th>Место</th><th>Участник</th><th>Результат</th><th>Время</th></tr></thead><tbody><tr v-for="item in data.items" :key="item.rank" :class="{ 'quiz-leaderboard__you': item.is_you }"><td>{{ item.rank }}</td><td>{{ item.name }}{{ item.is_you ? ' (вы)' : '' }}</td><td>{{ Math.round(item.score * 100) }}% · {{ item.correct }} из {{ item.total }}</td><td>{{ formatTrainingTime(item.duration_ms) }}</td></tr></tbody></table></div>
      <p v-if="data.my_entry && !data.items.some((item) => item.is_you)" class="text-3">Ваш результат: {{ Math.round(data.my_entry.score * 100) }}% за {{ formatTrainingTime(data.my_entry.duration_ms) }}.</p>
    </template>
  </section>
</template>
<style scoped>
.quiz-leaderboard { display: flex; flex-direction: column; gap: 16px; border-top: 1px solid var(--color-panel-border); padding-top: 24px; }
.quiz-leaderboard__scroll { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; text-align: left; }
th, td { padding: 12px; border-bottom: 1px solid var(--color-panel-border); }
.quiz-leaderboard__you { background: var(--color-active); }
</style>
