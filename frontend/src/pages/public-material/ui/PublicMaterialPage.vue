<script setup lang="ts">
import { onBeforeUnmount, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { createPublicMaterialApi, createMaterialApi, formatSize, type PublicMaterialDetail } from '@/entities/material'
import { useSessionStore } from '@/entities/session'
import { useMaterialLibraryStore } from '@/features/material-library'
import { NoteReader } from '@/features/read-notes'
import { QuizPanel, QuizLeaderboard } from '@/features/take-quiz'
import { BaseButton } from '@/shared/ui/button'
const route = useRoute()
const router = useRouter()
const session = useSessionStore()
const api = createPublicMaterialApi(session.request)
const privateApi = createMaterialApi(session.request)
const library = useMaterialLibraryStore()
const material = ref<PublicMaterialDetail | null>(null)
const tab = ref<'notes' | 'quiz' | 'ranking'>('notes')
const quizVisited = ref(false)
const rankingRevision = ref(0)
const loading = ref(false)
const importing = ref(false)
const downloading = ref(false)
const error = ref('')
let controller = new AbortController()
watch(() => [String(route.params.materialId), route.hash] as const, async ([id, hash], previous) => {
  if (material.value?.id === id && !hash && previous?.[1]) return
  controller.abort(); controller = new AbortController()
  const signal = controller.signal
  rankingRevision.value = 0; material.value = null; tab.value = 'notes'; quizVisited.value = false; error.value = ''; loading.value = true
  try { const share = new URLSearchParams(hash.slice(1)).get('share') || undefined; const data = await api.get(id, signal, share); if (!signal.aborted) { material.value = data; if (share) void router.replace({ hash: '' }) } }
  catch (reason) { if (!signal.aborted) error.value = reason instanceof Error ? reason.message : 'Не удалось загрузить материал.' }
  finally { if (!signal.aborted) loading.value = false }
}, { immediate: true })
async function save() {
  if (!material.value || importing.value) return
  importing.value = true; error.value = ''
  const signal = controller.signal
  try {
    const result = await api.import(material.value.id, AbortSignal.any([signal, AbortSignal.timeout(120000)]))
    if (signal.aborted) return
    const copy = await privateApi.get(result.material_id, signal)
    if (signal.aborted) return
    library.upsert(copy)
    void router.push({ name: 'material', params: { id: copy.id } })
  } catch (reason) { if (!signal.aborted) error.value = reason instanceof Error ? reason.message : 'Не удалось сохранить копию.' }
  finally { if (!signal.aborted) importing.value = false }
}
async function download() {
  if (!material.value || downloading.value) return
  downloading.value = true; error.value = ''
  const signal = controller.signal
  try {
    const blob = await api.download(material.value.id, signal)
    if (signal.aborted) return
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a'); link.href = url; link.download = material.value.filename; link.click()
    setTimeout(() => URL.revokeObjectURL(url), 60000)
  } catch (reason) { if (!signal.aborted) error.value = reason instanceof Error ? reason.message : 'Не удалось скачать лекцию.' }
  finally { if (!signal.aborted) downloading.value = false }
}
onBeforeUnmount(() => controller.abort())
</script>
<template>
  <div class="workspace-page">
    <RouterLink class="text-link text-3" to="/community">Вернуться в сообщество</RouterLink>
    <p v-if="loading" class="text-3 muted" role="status">Загружаем материал…</p>
    <p v-if="error" class="notice text-3 danger" role="alert">{{ error }}</p>
    <template v-if="material">
      <p v-if="material.visibility !== 'public'" class="text-3 muted">{{ material.visibility === 'groups' ? 'Доступ для выбранных групп' : 'Доступ по ссылке' }}</p>
      <header class="page-heading"><h1 class="title-3">{{ material.title }}</h1><p class="text-3 muted">Автор: {{ material.author }} · {{ formatSize(material.size_bytes) }}</p></header>
      <div class="public-material__actions">
        <BaseButton :loading="importing" @click="save">Сохранить в мою библиотеку</BaseButton>
        <BaseButton variant="transparent" :loading="downloading" @click="download">Скачать лекцию</BaseButton>
      </div>
      <p class="text-3 muted">В библиотеке будет ваша независимая копия лекции, конспекта и готового теста. Результаты других пользователей не копируются.</p>
      <div class="public-material__actions" aria-label="Разделы материала">
        <BaseButton :variant="tab === 'notes' ? 'yellow' : 'transparent'" :aria-pressed="tab === 'notes'" @click="tab = 'notes'">Конспект</BaseButton>
        <BaseButton :variant="tab === 'quiz' ? 'yellow' : 'transparent'" :aria-pressed="tab === 'quiz'" @click="tab = 'quiz'; quizVisited = true">Тест</BaseButton>
        <BaseButton v-if="material.quiz_id" :variant="tab === 'ranking' ? 'yellow' : 'transparent'" :aria-pressed="tab === 'ranking'" @click="tab = 'ranking'">Рейтинг</BaseButton>
      </div>
      <NoteReader v-show="tab === 'notes'" :content="material.note_content" :filename="material.filename" :public-material-id="material.id" />
      <QuizPanel v-if="quizVisited && material.quiz_id" v-show="tab === 'quiz'" :key="material.quiz_id" material-id="public" :public-quiz-id="material.quiz_id" hide-ranking @completed="rankingRevision++" />
      <section v-if="tab === 'ranking' && material.quiz_id" class="surface public-material__ranking"><QuizLeaderboard :quiz-id="material.quiz_id" :revision="rankingRevision" /></section>
      <div v-if="tab === 'quiz' && !material.quiz_id" class="surface empty-state"><h2 class="title-4">Автор пока не добавил тест</h2><p class="text-3 muted">Сохраните материал в библиотеку и создайте свой тест по конспекту.</p></div>
    </template>
  </div>
</template>
<style scoped>
.public-material__ranking { padding: 24px; }
.public-material__actions { display: flex; flex-wrap: wrap; gap: 16px; }
</style>
