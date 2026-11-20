<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { AlertCircle, BookOpen, ClipboardList, Download, RefreshCw } from 'lucide-vue-next'
import { MaterialProgress } from '@/widgets/material-progress'
import { NoteReader } from '@/features/read-notes'
import { QuizPanel } from '@/features/take-quiz'
import { useMaterialLibraryStore } from '@/features/material-library'
import { createMaterialApi, type Material } from '@/entities/material'
import { useSessionStore } from '@/entities/session'
import { BaseButton } from '@/shared/ui/button'
import { GenerationWait, clearGenerationWait } from '@/shared/ui/generation-wait'
const route = useRoute()
const router = useRouter()
const session = useSessionStore()
const library = useMaterialLibraryStore()
const api = createMaterialApi(session.request)
const creating = computed(() => route.meta.creatingMaterial === true)
const material = ref<Material | null>(null)
const content = ref('')
const loading = ref(true)
const working = ref(false)
const error = ref('')
const waitKey = computed(() => `studyai.wait.material.${String(route.params.id)}`)
const resultReady = computed(() => !!content.value.trim())
watch(resultReady, (ready) => {
  if (ready) clearGenerationWait(waitKey.value)
})
const tab = computed(() => (route.query.tab === 'quiz' ? 'quiz' : 'notes'))
const quizVisited = ref(tab.value === 'quiz')
watch(tab, (value) => {
  if (value === 'quiz') quizVisited.value = true
})
let controller = new AbortController()
let timer: ReturnType<typeof setTimeout> | undefined
let deadline = 0
let pendingPoll: AbortSignal | null = null
function schedule(signal: AbortSignal) {
  if (signal.aborted) return
  if (Date.now() < deadline) timer = setTimeout(() => void load(), 4000)
  else error.value = 'Материал ещё обрабатывается. Обновите статус немного позже.'
}
async function load() {
  const signal = controller.signal
  if (signal.aborted || pendingPoll === signal) return
  pendingPoll = signal
  clearTimeout(timer)
  const id = String(route.params.id)
  error.value = ''
  try {
    if (!material.value) {
      const item = await api.get(id, signal)
      if (signal.aborted) return
      material.value = item
    }
    const notes = await api.notesStatus(id, signal)
    if (signal.aborted) return
    material.value = { ...material.value!, status: notes.status }
    library.upsert(material.value)
    if (notes.status === 'failed') {
      error.value = 'Не удалось создать конспект. Запустите обработку повторно.'
      return
    }
    if (notes.status !== 'done' || !notes.note_id) {
      schedule(signal)
      return
    }
    if (!content.value) {
      const note = await api.notes(id, signal)
      if (signal.aborted) return
      if (!note.content.trim())
        throw new Error('Конспект пуст. Попробуйте запустить генерацию заново.')
      content.value = note.content
    }
  } catch (reason) {
    if (!signal.aborted)
      error.value = reason instanceof Error ? reason.message : 'Не удалось загрузить материал.'
  } finally {
    if (pendingPoll === signal) pendingPoll = null
    if (!signal.aborted) loading.value = false
  }
}
function refresh() {
  clearTimeout(timer)
  deadline = Date.now() + 10 * 60 * 1000
  loading.value = true
  void load()
}
async function regenerate() {
  if (!material.value || working.value) return
  working.value = true
  error.value = ''
  try {
    await api.regenerate(material.value.id)
    content.value = ''
    clearGenerationWait(waitKey.value)
    refresh()
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Не удалось запустить генерацию.'
  } finally {
    working.value = false
  }
}
function selectTab(value: string) {
  void router.replace({ query: value === 'quiz' ? { tab: value } : {} })
}
watch(
  () => `${String(route.name)}:${String(route.params.id ?? '')}`,
  () => {
    clearTimeout(timer)
    controller.abort()
    controller = new AbortController()
    material.value = null
    pendingPoll = null
    content.value = ''
    error.value = ''
    loading.value = true
    quizVisited.value = tab.value === 'quiz'
    deadline = Date.now() + 10 * 60 * 1000
    void load()
  },
  { immediate: true }
)
onBeforeUnmount(() => {
  clearTimeout(timer)
  controller.abort()
})
</script>

<template>
  <div class="workspace-page material-page">
    <header class="page-heading">
      <h1 class="title-1">Создать материал</h1>
      <p class="text-1 muted">
        {{ material?.original_filename || 'Загрузите лекцию, чтобы получить конспект' }}
      </p>
    </header>
    <MaterialProgress :step="resultReady ? 3 : 2" :compact="creating" />
    <div v-if="error" class="notice text-3" role="alert">
      <AlertCircle :size="24" />
      <p>{{ error }}</p>
      <BaseButton variant="transparent" :disabled="loading" @click="refresh"
        >Обновить статус</BaseButton
      ><BaseButton v-if="material?.status === 'failed'" :loading="working" @click="regenerate"
        >Повторить обработку</BaseButton
      >
    </div>
    <section v-if="loading && !resultReady" class="surface empty-state" role="status">
      <BookOpen :size="56" />
      <h2 class="title-4">Загружаем материал…</h2>
    </section>
    <section
      v-else-if="!resultReady && !error"
      class="surface empty-state"
      aria-labelledby="processing-title"
    >
      <BookOpen :size="56" />
      <h2 id="processing-title" class="title-4" role="status">Готовим ваш конспект</h2>
      <p class="text-2 muted">
        Извлекаем текст и выделяем главное. Тест можно будет создать отдельно.
      </p>
      <p class="text-3 muted">Можно закрыть страницу и вернуться к материалу позже.</p>
      <GenerationWait :storage-key="waitKey" />
    </section>
    <template v-if="resultReady">
      <p v-if="tab === 'notes'" class="notice text-3">
        Конспект готов. Если захотите проверить знания, откройте вкладку «Тест» и нажмите «Создать
        тест».
      </p>
      <div class="material-page__toolbar">
        <div class="material-page__tabs" aria-label="Содержимое материала">
          <button
            class="material-page__tab text-2"
            :class="{ 'material-page__tab--active': tab === 'notes' }"
            :aria-pressed="tab === 'notes'"
            @click="selectTab('notes')"
          >
            <BookOpen />Конспект</button
          ><button
            class="material-page__tab text-2"
            :class="{ 'material-page__tab--active': tab === 'quiz' }"
            :aria-pressed="tab === 'quiz'"
            @click="selectTab('quiz')"
          >
            <ClipboardList />Тест
          </button>
        </div>
        <div class="material-page__tools">
          <a
            v-if="material?.download_url"
            class="text-link text-3"
            :href="material.download_url"
            target="_blank"
            rel="noopener noreferrer"
            ><Download :size="20" />Исходный файл</a
          ><button
            class="icon-button"
            :disabled="working"
            aria-label="Сгенерировать конспект заново"
            @click="regenerate"
          >
            <RefreshCw />
          </button>
        </div>
      </div>
      <NoteReader
        v-show="tab === 'notes'"
        :content="content"
        :filename="material?.original_filename"
        :material-id="String(route.params.id)"
      />
      <QuizPanel
        v-if="quizVisited"
        v-show="tab === 'quiz'"
        :key="String(route.params.id)"
        :material-id="String(route.params.id)"
      />
    </template>
  </div>
</template>
<style scoped>
.material-page__toolbar,
.material-page__tabs,
.material-page__tools {
  display: flex;
  align-items: center;
  gap: 20px;
}
.material-page__toolbar {
  justify-content: space-between;
}
.material-page__tab {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 20px;
  border: 0;
  border-radius: var(--radius-card);
  background: transparent;
  color: var(--color-text-secondary);
}
.material-page__tab--active {
  color: var(--color-yellow);
  background: var(--color-active);
}
.material-page > .notice {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
}
@media (max-width: 768px) {
  .material-page__toolbar {
    flex-wrap: wrap;
    gap: 12px;
  }
  .material-page__tabs {
    flex-wrap: wrap;
  }
}
</style>
