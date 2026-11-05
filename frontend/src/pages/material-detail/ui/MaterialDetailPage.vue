<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  ArrowLeft,
  BookOpen,
  CalendarDays,
  ClipboardList,
  Download,
  FileText,
  Info,
  Pencil,
  RefreshCw,
  Star,
  Trash2,
} from 'lucide-vue-next'
import { NoteReader } from '@/features/read-notes'
import { QuizPanel } from '@/features/take-quiz'
import { useMaterialLibraryStore } from '@/features/material-library'
import {
  createMaterialApi,
  formatSize,
  materialStatusLabel,
  type Material,
  type Note,
  type NoteStatus,
  type Quiz,
  type QuizStatus,
} from '@/entities/material'
import { useSessionStore } from '@/entities/session'
import { BaseButton } from '@/shared/ui/button'
import { designAssets } from '@/shared/assets'

const route = useRoute()
const router = useRouter()
const api = createMaterialApi(useSessionStore().request)
const library = useMaterialLibraryStore()
const material = ref<Material | null>(null)
const note = ref<Note | null>(null)
const notesStatus = ref<NoteStatus | null>(null)
const quizStatus = ref<QuizStatus | null>(null)
const quiz = ref<Quiz | null>(null)
const loading = ref(true)
const error = ref('')
const quizVisited = ref(false)
const tab = computed(() =>
  route.query.tab === 'quiz' ? 'quiz' : route.query.tab === 'info' ? 'info' : 'notes'
)
const title = computed(
  () => material.value?.original_filename.replace(/\.[^.]+$/, '') || 'Материал'
)
const date = computed(() =>
  material.value
    ? new Intl.DateTimeFormat('ru-RU', { day: 'numeric', month: 'long', year: 'numeric' }).format(
        new Date(material.value.created_at)
      )
    : '—'
)
const quizCount = computed(() => quiz.value?.questions.length)
const quizGenerating = computed(
  () => quizStatus.value?.status === 'processing' && (!!quizStatus.value.quiz_id)
)
let controller = new AbortController()
let timer: ReturnType<typeof setTimeout> | undefined
let pending: AbortSignal | null = null
let deadline = 0

function selectTab(value: string) {
  if (value === 'quiz') quizVisited.value = true
  void router.replace({ query: value === 'notes' ? {} : { tab: value } })
}
async function load() {
  const signal = controller.signal
  if (signal.aborted || pending === signal) return
  pending = signal
  clearTimeout(timer)
  error.value = ''
  const id = String(route.params.id)
  try {
    if (!material.value) {
      const data = await api.get(id, signal)
      if (signal.aborted) return
      material.value = data
    }
    const [notes, test] = await Promise.all([
      api.notesStatus(id, signal),
      api.quizStatus(id, signal),
    ])
    if (signal.aborted) return
    notesStatus.value = notes
    quizStatus.value = test
    library.upsert({ ...material.value!, status: notes.status })
    if (notes.status === 'done' && notes.note_id && !note.value) {
      const data = await api.notes(id, signal)
      if (signal.aborted) return
      note.value = data
    }
    if (test.quiz_id && test.status === 'done' && quiz.value?.id !== test.quiz_id) {
      const data = await api.quiz(id, signal)
      if (signal.aborted) return
      quiz.value = data
      library.quizReady[id] = true
    }
    if (notes.status === 'failed') error.value = 'Обработка конспекта завершилась ошибкой.'
    const inProgress =
      ['uploaded', 'processing'].includes(notes.status) ||
      (test.status === 'processing' && (!!test.quiz_id))
    if (inProgress && Date.now() < deadline) timer = setTimeout(() => void load(), 4000)
    else if (inProgress)
      error.value = 'Обработка занимает больше времени. Обновите статус немного позже.'
  } catch (reason) {
    if (!signal.aborted)
      error.value = reason instanceof Error ? reason.message : 'Не удалось загрузить материал.'
  } finally {
    if (pending === signal) pending = null
    if (!signal.aborted) loading.value = false
  }
}
function refresh() {
  deadline = Date.now() + 10 * 60 * 1000
  void load()
}
watch(tab, (value) => {
  if (value === 'quiz') quizVisited.value = true
})
watch(
  () => String(route.params.id),
  () => {
    clearTimeout(timer)
    controller.abort()
    controller = new AbortController()
    pending = null
    material.value = null
    note.value = null
    notesStatus.value = null
    quizStatus.value = null
    quiz.value = null
    loading.value = true
    error.value = ''
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
  <div class="material-detail">
    <RouterLink to="/materials" class="material-detail__back text-link text-4"
      ><ArrowLeft :size="20" />Мои материалы</RouterLink
    >
    <header class="material-detail__header">
      <div
        class="material-detail__thumbnail"
        :style="{ backgroundImage: `url(${designAssets.heroBackground})` }"
        aria-hidden="true"
      />
      <div class="material-detail__identity">
        <h1 class="title-4">{{ title }}</h1>
        <div class="material-detail__meta text-4 muted">
          <span><FileText :size="17" />{{ material?.original_filename || 'Загрузка…' }}</span
          ><span><CalendarDays :size="17" />{{ date }}</span
          ><span v-if="material"><FileText :size="17" />{{ formatSize(material.size_bytes) }}</span>
        </div>
      </div>
      <div class="material-detail__actions">
        <button
          class="icon-button material-detail__action"
          type="button"
          disabled
          aria-label="Добавить в избранное"
          title="Избранное пока недоступно"
        >
          <Star :size="22" /></button
        ><button
          class="icon-button material-detail__action"
          type="button"
          disabled
          aria-label="Удалить материал"
          title="Удаление пока недоступно"
        >
          <Trash2 :size="22" /></button
        ><BaseButton
          variant="transparent"
          class="material-detail__edit"
          disabled
          title="Редактирование материала пока недоступно"
          ><template #icon-left><Pencil /></template>Редактировать</BaseButton
        >
      </div>
    </header>
    <nav class="material-detail__tabs" aria-label="Разделы материала">
      <button
        v-for="item in [
          { id: 'notes', title: 'Конспект', icon: BookOpen },
          { id: 'quiz', title: 'Тест', icon: ClipboardList },
          { id: 'info', title: 'Информация', icon: Info },
        ]"
        :key="item.id"
        class="material-detail__tab text-4"
        :class="{ 'material-detail__tab--active': tab === item.id }"
        :aria-pressed="tab === item.id"
        @click="selectTab(item.id)"
      >
        <component :is="item.icon" :size="22" />{{ item.title }}
      </button>
    </nav>
    <div v-if="error" class="notice material-detail__error text-3" role="alert">
      <p>{{ error }}</p>
      <button class="text-link" type="button" @click="refresh">
        <RefreshCw :size="18" />Обновить
      </button>
    </div>
    <div class="material-detail__layout">
      <div class="material-detail__main">
        <div v-if="loading && !material" class="surface empty-state" role="status">
          <BookOpen :size="40" />
          <p class="text-2 muted">Загружаем материал…</p>
        </div>
        <template v-else>
          <NoteReader
            v-if="note?.content"
            v-show="tab === 'notes'"
            detailed
            :content="note.content"
            :filename="material?.original_filename"
            :material-id="String(route.params.id)"
          />
          <div v-else-if="tab === 'notes'" class="surface empty-state">
            <BookOpen :size="40" />
            <h2 class="title-4">
              {{
                notesStatus?.status === 'failed' ? 'Конспект недоступен' : 'Конспект обрабатывается'
              }}
            </h2>
            <p class="text-3 muted">
              {{
                notesStatus?.status === 'failed'
                  ? 'Вернитесь к материалам или обновите статус.'
                  : 'Готовый конспект появится здесь автоматически.'
              }}
            </p>
          </div>
          <QuizPanel
            v-if="quizVisited"
            v-show="tab === 'quiz'"
            :key="String(route.params.id)"
            :material-id="String(route.params.id)"
            :initial-quiz="quiz || undefined"
            :generation-pending="quizGenerating"
          />
          <section v-if="tab === 'info'" class="surface material-detail__information">
            <h2 class="title-4">Информация о материале</h2>
            <dl class="text-3">
              <div>
                <dt>Название файла</dt>
                <dd>{{ material?.original_filename || '—' }}</dd>
              </div>
              <div>
                <dt>Дата загрузки</dt>
                <dd>{{ date }}</dd>
              </div>
              <div>
                <dt>Формат</dt>
                <dd>{{ material?.original_filename.split('.').pop()?.toUpperCase() || '—' }}</dd>
              </div>
              <div>
                <dt>Размер</dt>
                <dd>{{ material ? formatSize(material.size_bytes) : '—' }}</dd>
              </div>
              <div>
                <dt>Статус конспекта</dt>
                <dd>{{ notesStatus ? materialStatusLabel[notesStatus.status] : '—' }}</dd>
              </div>
              <div>
                <dt>Количество вопросов</dt>
                <dd>{{ quizCount ?? '—' }}</dd>
              </div>
            </dl>
            <a
              v-if="material?.download_url"
              class="text-link text-3"
              :href="material.download_url"
              target="_blank"
              rel="noopener noreferrer"
              ><Download :size="20" />Скачать исходный файл</a
            >
          </section>
        </template>
      </div>
    </div>
  </div>
</template>

<style scoped>
.material-detail {
  display: flex;
  flex-direction: column;
  gap: 20px;
  width: 100%;
}
.material-detail__back {
  align-self: flex-start;
  color: var(--color-text-secondary);
}
.material-detail__header {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 0 4px;
}
.material-detail__thumbnail {
  width: 104px;
  height: 92px;
  flex-shrink: 0;
  border-radius: var(--radius-card);
  background-size: cover;
  background-position: 75% 50%;
  border: 1px solid var(--color-border-muted);
}
.material-detail__identity {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-width: 0;
  flex: 1;
}
.material-detail__identity h1 {
  overflow-wrap: anywhere;
}
.material-detail__meta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px 24px;
}
.material-detail__meta span {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  overflow-wrap: anywhere;
}
.material-detail__meta svg {
  flex-shrink: 0;
}
.material-detail__actions {
  display: flex;
  align-items: center;
  gap: 14px;
}
.material-detail__action {
  border: 1px solid var(--color-border-muted);
  border-radius: 12px;
  width: 46px;
  height: 42px;
}
.material-detail__action:disabled {
  opacity: 0.65;
}
.material-detail__edit {
  min-height: 42px;
  padding: 10px 20px;
}
.material-detail__tabs {
  display: flex;
  align-self: flex-start;
  align-items: center;
  border-radius: var(--border-radius-lg);
  background: color-mix(in srgb, var(--color-panel) 85%, transparent);
  border: 1px solid var(--color-panel-border);
  padding: 3px;
}
.material-detail__tab {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 14px;
  min-width: 150px;
  padding: 12px 24px;
  border: 0;
  border-radius: var(--border-radius-lg);
  background: transparent;
  color: var(--color-text-secondary);
}
.material-detail__tab--active {
  background: linear-gradient(
    135deg,
    var(--color-yellow),
    color-mix(in srgb, var(--color-yellow) 85%, var(--color-orange))
  );
  color: var(--color-background);
  font-weight: var(--font-weight-semibold);
}
.material-detail__layout {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  gap: 24px;
}
.material-detail__main {
  flex: 1 1 520px;
  min-width: 0;
}
.material-detail__information {
  display: flex;
  flex-direction: column;
  gap: 24px;
  padding: 28px;
  border-width: 1px;
}
.material-detail__information dl {
  display: flex;
  flex-direction: column;
  margin: 0;
}
.material-detail__information dl > div {
  display: flex;
  justify-content: space-between;
  gap: 28px;
  padding: 18px 0;
  border-bottom: 1px solid var(--color-panel-border);
}
.material-detail__information dt {
  color: var(--color-text-secondary);
}
.material-detail__information dd {
  margin: 0;
  text-align: right;
  overflow-wrap: anywhere;
  min-width: 0;
}
.material-detail__error {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
}
@media (max-width: 768px) {
  .material-detail__header {
    flex-wrap: wrap;
  }
  .material-detail__thumbnail {
    width: 72px;
    height: 64px;
  }
  .material-detail__actions {
    flex-wrap: wrap;
  }
  .material-detail__tabs {
    width: 100%;
  }
  .material-detail__tab {
    flex: 1 1 auto;
    min-width: 0;
    padding: 10px 12px;
    gap: 8px;
  }
  .material-detail__information dl > div {
    flex-wrap: wrap;
    gap: 4px 20px;
    padding: 12px 0;
  }
  .material-detail__information dd {
    text-align: left;
  }
  .material-detail__error {
    flex-wrap: wrap;
  }
  .material-detail__information {
    padding: 20px 16px;
  }
}
</style>
