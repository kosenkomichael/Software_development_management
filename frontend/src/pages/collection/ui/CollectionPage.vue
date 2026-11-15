<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { createPublicQuizApi, createPublicMaterialApi, formatSize, formatTrainingTime, type PublicMaterialItem, type PublicAttemptItem } from '@/entities/material'
import { useSessionStore } from '@/entities/session'
import { BaseButton } from '@/shared/ui/button'
const api = createPublicQuizApi(useSessionStore().request)
const materialsApi = createPublicMaterialApi(useSessionStore().request)
const items = ref<PublicMaterialItem[]>([])
const history = ref<PublicAttemptItem[]>([])
const tab = ref<'quizzes' | 'history'>('quizzes')
const page = ref(0)
const total = ref(0)
const loading = ref(false)
const error = ref('')
let controller = new AbortController()
const date = (value: string) => new Intl.DateTimeFormat('ru-RU', { day: 'numeric', month: 'long', year: 'numeric', hour: '2-digit', minute: '2-digit' }).format(new Date(value))
async function load(reset = false) {
  const signal = controller.signal
  loading.value = true; error.value = ''
  const next = reset ? 1 : page.value + 1
  try {
    if (tab.value === 'quizzes') {
      const data = await materialsApi.list(next, signal)
      if (signal.aborted) return
      items.value = reset ? data.items : [...items.value, ...data.items]; total.value = data.total
    } else {
      const data = await api.attempts(undefined, next, signal)
      if (signal.aborted) return
      history.value = reset ? data.items : [...history.value, ...data.items]; total.value = data.total
    }
    page.value = next
  } catch (reason) { if (!signal.aborted) error.value = reason instanceof Error ? reason.message : 'Не удалось загрузить список.' }
  finally { if (!signal.aborted) loading.value = false }
}
function changeTab(value: 'quizzes' | 'history') {
  controller.abort(); controller = new AbortController()
  tab.value = value; items.value = []; history.value = []; total.value = 0; page.value = 0
  void load(true)
}
onMounted(() => void load(true))
onBeforeUnmount(() => controller.abort())
</script>
<template>
  <div class="workspace-page">
    <header class="page-heading"><h1 class="title-1">Сообщество</h1><p class="text-1 muted">Лекции, конспекты и тесты, которыми поделились другие пользователи</p></header>
    <div class="community__tabs">
      <BaseButton :variant="tab === 'quizzes' ? 'yellow' : 'transparent'" :aria-pressed="tab === 'quizzes'" @click="changeTab('quizzes')">Учебные материалы</BaseButton>
      <BaseButton :variant="tab === 'history' ? 'yellow' : 'transparent'" :aria-pressed="tab === 'history'" @click="changeTab('history')">Мои прохождения</BaseButton>
      <BaseButton variant="transparent" :disabled="loading" @click="load(true)">Обновить</BaseButton>
    </div>
    <p v-if="error" class="notice text-3 danger" role="alert">{{ error }}</p>
    <p v-if="loading" class="text-3 muted" role="status">Загружаем…</p>
    <div v-if="!loading && !error && !total" class="surface empty-state">
      <h2 class="title-4">{{ tab === 'quizzes' ? 'Пока нет опубликованных материалов' : 'Вы ещё не проходили публичные тесты' }}</h2>
      <p class="text-3 muted">{{ tab === 'quizzes' ? 'Материалом можно поделиться кнопкой «Поделиться материалом» в его меню.' : 'Результаты и выбранные ответы появятся здесь после завершения теста.' }}</p>
    </div>
    <div v-if="tab === 'quizzes'" class="community__grid">
      <article v-for="item in items" :key="item.id" class="surface community__card">
        <h2 class="title-4">{{ item.title }}</h2>
        <p v-if="item.visibility !== 'public'" class="text-4 muted">{{ item.visibility === 'groups' ? 'Для выбранных групп' : 'По ссылке' }}</p>
        <p class="text-3 muted">Автор: {{ item.author }} · {{ formatSize(item.size_bytes) }}</p>
        <p class="text-3 muted">Лекция · Конспект{{ item.has_quiz ? ' · Тест' : '' }}</p>
        <p class="text-4 muted">{{ date(item.published_at) }}</p>
        <RouterLink class="text-link text-3" :to="{ name: 'public-material', params: { materialId: item.id } }">Открыть материал</RouterLink>
      </article>
    </div>
    <div v-else class="community__grid">
      <article v-for="item in history" :key="item.id" class="surface community__card">
        <h2 class="title-4">{{ item.title }}</h2>
        <p class="text-3">{{ Math.round(item.score * 100) }}% · {{ item.correct }} из {{ item.total }}<template v-if="item.duration_ms != null"> · {{ formatTrainingTime(item.duration_ms) }}</template></p>
        <p class="text-4 muted">{{ date(item.created_at) }}</p>
        <RouterLink class="text-link text-3" :to="{ name: 'public-attempt', params: { attemptId: item.id } }">Посмотреть ответы</RouterLink>
      </article>
    </div>
    <BaseButton v-if="(tab === 'quizzes' ? items.length : history.length) < total" variant="transparent" :loading="loading" @click="load()">Показать ещё</BaseButton>
  </div>
</template>
<style scoped>
.community__tabs { display: flex; flex-wrap: wrap; gap: 12px; }
.community__grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 300px), 1fr)); gap: 24px; }
.community__card { padding: 24px; display: flex; flex-direction: column; gap: 16px; overflow-wrap: anywhere; }
</style>
