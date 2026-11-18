<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, ArrowRight, CheckCircle2, CircleAlert, ClipboardList, RefreshCw } from 'lucide-vue-next'
import { useSessionStore } from '@/entities/session'
import {
  createMaterialApi,
  createPublicQuizApi,
  formatTrainingTime,
  type Quiz,
  type QuizResult,
  type QuizAttemptSummary,
  type SubmittedAnswer,
} from '@/entities/material'
import QuizLeaderboard from './QuizLeaderboard.vue'
import { ApiError } from '@/shared/api'
import { BaseButton } from '@/shared/ui/button'
import { GenerationWait, clearGenerationWait } from '@/shared/ui/generation-wait'
const props = defineProps<{
  materialId: string
  publicQuizId?: string
  savedPublicAttemptId?: string
  hideRanking?: boolean
  demo?: Quiz
  demoAnswers?: Record<string, string[]>
  initialQuiz?: Quiz
  generationPending?: boolean
}>()
const emit = defineEmits<{ completed: [] }>()
const route = useRoute()
const router = useRouter()
const privateApi = createMaterialApi(useSessionStore().request)
const publicApi = createPublicQuizApi(useSessionStore().request)
const publicMode = computed(() => !!props.publicQuizId || !!props.savedPublicAttemptId)
const api = {
  ...privateApi,
  attempts: (id: string, page = 1, signal?: AbortSignal) => publicMode.value ? publicApi.attempts(props.publicQuizId, page, signal) : privateApi.attempts(id, page, signal),
  attempt: (id: string, attemptId: string, signal?: AbortSignal) => publicMode.value ? publicApi.attempt(attemptId, signal) : privateApi.attempt(id, attemptId, signal),
  submit: (id: string, answers: SubmittedAnswer[], quizId: string) => publicMode.value ? publicApi.submit(quizId, answers, training.value?.runId) : privateApi.submit(id, answers, quizId),
}
const quiz = ref<Quiz | null>(null)
const activeQuiz = ref<Quiz | null>(null)
const training = ref<{ runId: string; elapsed: number; received: number } | null>(null)
const starting = ref(false)
const rankingVisible = ref(false)
const rankingRevision = ref(0)
const clock = ref(performance.now())
function cancelTraining() {
  const run = training.value
  if (!run || result.value || submitting.value || !props.publicQuizId) return
  training.value = null
  answers.value = {}
  try { sessionStorage.removeItem(`studyai.training.answers.${run.runId}`) } catch { /* Storage is optional. */ }
  void publicApi.cancel(props.publicQuizId, run.runId).catch(() => undefined)
}
window.addEventListener('pagehide', cancelTraining)
const heartbeatClock = setInterval(() => {
  const run = training.value
  if (!run || result.value || submitting.value || !props.publicQuizId) return
  void publicApi.heartbeat(props.publicQuizId, run.runId).catch((reason: unknown) => {
    if (!(reason instanceof ApiError) || reason.status !== 409) return
    if (training.value?.runId !== run.runId) return
    cancelTraining()
    error.value = 'Тренировка прервана. Начните новую попытку.'
  })
}, 30000)
const trainingClock = setInterval(() => { clock.value = performance.now() }, 1000)
const trainingElapsed = computed(() => training.value ? Math.max(0, training.value.elapsed + clock.value - training.value.received) : 0)
async function startTraining() {
  if (starting.value || !props.publicQuizId || !quiz.value) return
  starting.value = true; error.value = ''
  const signal = controller.signal
  try {
    const run = await publicApi.start(props.publicQuizId, signal)
    if (signal.aborted) return
    const received = performance.now()
    training.value = { runId: run.run_id, elapsed: Date.parse(run.server_time) - Date.parse(run.started_at), received }
    clock.value = received
    answers.value = {}
  } catch (reason) { if (!signal.aborted) error.value = reason instanceof Error ? reason.message : 'Не удалось начать тренировку.' }
  finally { if (!signal.aborted) starting.value = false }
}
const attempts = ref<QuizAttemptSummary[]>([])
const attemptsTotal = ref(0)
const historyPage = ref(0)
const historyVisible = ref(false)
const historyLoading = ref(false)
const historyOpening = ref(false)
const historyError = ref('')
const viewingAttempt = ref<QuizAttemptSummary | null>(null)
const formatAttemptDate = (date: string) => new Intl.DateTimeFormat('ru-RU', {
  day: 'numeric', month: 'long', year: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit',
}).format(new Date(date))
const current = ref(0)
const answers = ref<Record<string, string[]>>({})
const result = ref<QuizResult | null>(null)
const scorePercent = computed(() => Math.round((result.value?.score ?? 0) * 100))
const scoreLevel = computed(() => {
  if (scorePercent.value >= 80) return { name: 'high', label: 'Хороший результат', icon: CheckCircle2 }
  if (scorePercent.value >= 50) return { name: 'medium', label: 'Стоит повторить ошибки', icon: CircleAlert }
  return { name: 'low', label: 'Стоит повторить материал', icon: CircleAlert }
})
const loading = ref(false)
const processing = ref(false)
const submitting = ref(false)
const error = ref('')
const waitKey = computed(() => `studyai.wait.quiz.${props.materialId}`)
let timer: ReturnType<typeof setTimeout> | undefined
let controller = new AbortController()
let deadline = 0
let historyRevision = 0
const question = computed(() => quiz.value?.questions[current.value])
const questionResult = computed(() =>
  result.value?.results.find((item) => item.question_id === question.value?.id)
)
function stop() {
  clearTimeout(timer)
  controller.abort()
}
function answered(id: string) {
  return !!answers.value[id]?.length
}
function select(answerId: string, checked: boolean) {
  const item = question.value
  if (!item || result.value) return
  if (item.question_type === 'multiple')
    answers.value[item.id] = checked
      ? [...(answers.value[item.id] ?? []), answerId]
      : (answers.value[item.id] ?? []).filter((id) => id !== answerId)
  else answers.value[item.id] = [answerId]
}
function selectQuestion(index: number) {
  if (submitting.value) return
  current.value = index
  error.value = ''
}
function restart() {
  if (publicMode.value) { cancelTraining(); training.value = null }
  if (route.query.attempt) void router.replace({ query: { ...route.query, attempt: undefined } })
  if (viewingAttempt.value) {
    quiz.value = activeQuiz.value
    if (!quiz.value) void load(controller.signal)
  }
  viewingAttempt.value = null
  result.value = null
  answers.value = {}
  selectQuestion(0)
}
function toggleHistory() {
  historyVisible.value = !historyVisible.value
  if (historyVisible.value) void loadHistory(true)
}
async function loadHistory(reset = false) {
  const revision = ++historyRevision
  const signal = controller.signal
  historyLoading.value = true
  historyError.value = ''
  try {
    const page = reset ? 1 : historyPage.value + 1
    const response = await api.attempts(props.materialId, page, signal)
    if (signal.aborted || revision !== historyRevision) return
    attempts.value = reset ? response.items : [...attempts.value, ...response.items]
    attemptsTotal.value = response.total
    historyPage.value = page
  } catch (reason) {
    if (!signal.aborted && revision === historyRevision) historyError.value = reason instanceof Error ? reason.message : 'Не удалось загрузить историю.'
  } finally {
    if (!signal.aborted && revision === historyRevision) historyLoading.value = false
  }
}
async function openAttempt(attempt: Pick<QuizAttemptSummary, 'id'>) {
  if (submitting.value || loading.value || historyOpening.value) return
  cancelTraining()
  const signal = controller.signal
  historyOpening.value = true
  historyError.value = ''
  clearTimeout(timer)
  try {
    const saved = await api.attempt(props.materialId, attempt.id, signal)
    if (signal.aborted) return
    quiz.value = saved.quiz
    answers.value = Object.fromEntries(saved.answers.map((answer) => [answer.question_id, answer.selected_ids]))
    result.value = saved.result
    viewingAttempt.value = saved
    historyVisible.value = false
    current.value = 0
    processing.value = false
  } catch (reason) {
    if (!signal.aborted) historyError.value = reason instanceof Error ? reason.message : 'Не удалось открыть попытку.'
  } finally {
    if (!signal.aborted) historyOpening.value = false
  }
}
function refreshQuiz() {
  if (publicMode.value) { cancelTraining(); training.value = null }
  if (route.query.attempt) void router.replace({ query: { ...route.query, attempt: undefined } })
  quiz.value = activeQuiz.value
  viewingAttempt.value = null
  result.value = null
  answers.value = {}
  current.value = 0
  void load(controller.signal)
}
function schedule(signal: AbortSignal) {
  if (signal.aborted) return
  if (Date.now() > deadline) {
    processing.value = false
    error.value =
      'Генерация занимает больше времени. Нажмите «Обновить», чтобы проверить результат.'
    return
  }
  timer = setTimeout(() => void load(signal), 4000)
}
async function load(signal: AbortSignal) {
  if (publicMode.value) {
    if (props.savedPublicAttemptId) { await openAttempt({ id: props.savedPublicAttemptId }); return }
    loading.value = true; error.value = ''
    try {
      const loaded = await publicApi.quiz(props.publicQuizId!, signal)
      if (!signal.aborted) { quiz.value = loaded; activeQuiz.value = loaded; processing.value = false }
    } catch (reason) { if (!signal.aborted) error.value = reason instanceof Error ? reason.message : 'Не удалось загрузить публичный тест.' }
    finally { if (!signal.aborted) loading.value = false }
    return
  }
  if (signal.aborted) return
  clearTimeout(timer)
  error.value = ''
  loading.value = true
  try {
    const status = await api.quizStatus(props.materialId, signal)
    if (signal.aborted) return
    if (status.quiz_id && status.status === 'done') {
      const loaded = await api.quiz(props.materialId, signal)
      if (signal.aborted) return
      quiz.value = loaded
      activeQuiz.value = loaded
      processing.value = false
      clearGenerationWait(waitKey.value)
    } else if (status.status === 'failed') {
      processing.value = false
      error.value = 'Не удалось создать тест. Попробуйте запустить генерацию ещё раз.'
    } else if (status.quiz_id || processing.value) {
      processing.value = true
      schedule(signal)
    }
  } catch (reason) {
    if (!signal.aborted) {
      processing.value = false
      error.value = reason instanceof Error ? reason.message : 'Не удалось загрузить тест.'
    }
  } finally {
    if (!signal.aborted) {
      loading.value = false
      const id = route.query.attempt
      if (typeof id === 'string' && viewingAttempt.value?.id !== id && !props.demo) void openAttempt({ id })
    }
  }
}
async function generate() {
  if (loading.value || processing.value) return
  loading.value = true
  error.value = ''
  const signal = controller.signal
  try {
    await api.generateQuiz(props.materialId)
    if (signal.aborted) return
    clearGenerationWait(waitKey.value)
    processing.value = true
    deadline = Date.now() + 10 * 60 * 1000
    schedule(signal)
  } catch (reason) {
    if (!signal.aborted)
      error.value = reason instanceof Error ? reason.message : 'Не удалось запустить генерацию.'
  } finally {
    if (!signal.aborted) loading.value = false
  }
}
async function submit() {
  if (!quiz.value || submitting.value || result.value) return
  error.value = ''
  submitting.value = true
  const signal = controller.signal
  const submitted: SubmittedAnswer[] = quiz.value.questions.map((item) => ({
    question_id: item.id,
    selected_ids: answers.value[item.id] ?? [],
  }))
  try {
    if (props.demo) {
      const results = submitted.map((item) => {
        const correctIds = props.demoAnswers?.[item.question_id] ?? []
        return {
          question_id: item.question_id,
          is_correct: [...item.selected_ids].sort().join(',') === [...correctIds].sort().join(','),
          correct_ids: correctIds,
        }
      })
      const correct = results.filter((item) => item.is_correct).length
      result.value = {
        correct,
        total: results.length,
        score: results.length ? correct / results.length : 0,
        results,
      }
    } else {
      const response = await api.submit(props.materialId, submitted, quiz.value.id)
      if (signal.aborted) return
      result.value = response
      rankingRevision.value++
      emit('completed')
      if (training.value) {
        try { sessionStorage.removeItem(`studyai.training.answers.${training.value.runId}`) } catch { /* Storage is optional. */ }
      }
      if (historyVisible.value) void loadHistory(true)
    }
    current.value = 0
  } catch (reason) {
    if (!signal.aborted)
      error.value = reason instanceof Error ? reason.message : 'Не удалось отправить ответы.'
  } finally {
    if (!signal.aborted) submitting.value = false
  }
}
watch(
  () => `${props.materialId}:${props.publicQuizId ?? ''}:${props.savedPublicAttemptId ?? ''}`,
  () => {
    cancelTraining()
    stop()
    controller = new AbortController()
    current.value = 0
    quiz.value = props.demo ?? props.initialQuiz ?? null
    activeQuiz.value = quiz.value
    training.value = null
    starting.value = false
    rankingVisible.value = false
    attempts.value = []
    attemptsTotal.value = 0
    historyPage.value = 0
    historyVisible.value = false
    historyLoading.value = false
    historyOpening.value = false
    historyError.value = ''
    viewingAttempt.value = null
    result.value = null
    answers.value = {}
    processing.value = !!props.generationPending
    submitting.value = false
    deadline = Date.now() + 10 * 60 * 1000
    if (!props.demo && !props.initialQuiz) void load(controller.signal)
    else if (!props.demo && typeof route.query.attempt === 'string') void openAttempt({ id: route.query.attempt })
  },
  { immediate: true }
)
watch(() => route.query.attempt, (id) => {
  if (typeof id === 'string' && !props.demo && !loading.value) void openAttempt({ id })
})
onBeforeUnmount(() => { cancelTraining(); stop(); clearInterval(trainingClock); clearInterval(heartbeatClock); window.removeEventListener('pagehide', cancelTraining) })
</script>

<template>
  <section class="surface quiz-panel" :aria-busy="loading || submitting">
    <header class="section-heading">
      <h2 class="title-3 quiz-panel__heading"><ClipboardList :size="38" />{{ publicMode ? quiz?.title || 'Тест' : 'Тест' }}</h2>
      <button
        v-if="!demo && !submitting"
        class="icon-button"
        :disabled="loading || historyOpening"
        aria-label="Обновить тест"
        @click="refreshQuiz"
      >
        <RefreshCw />
      </button>
    </header>
    <p v-if="demo" class="notice text-3">Демонстрационный тест. Результат не сохраняется.</p>
    <p v-if="error" class="notice danger text-3" role="alert">{{ error }}</p>
    <div v-if="processing || (loading && !quiz)" class="empty-state">
      <ClipboardList :size="48" />
      <h3 class="title-4">
        {{ processing ? 'Создаём тест по вашему материалу' : 'Загружаем тест…' }}
      </h3>
      <GenerationWait v-if="processing" :storage-key="waitKey" />
      <p class="text-3 muted">Можно вернуться к конспекту. Генерация продолжится на сервере.</p>
    </div>
    <div v-else-if="!quiz || !quiz.questions.length" class="empty-state">
      <ClipboardList :size="48" />
      <h3 class="title-4">{{ publicMode ? 'Тест недоступен' : 'Проверьте свои знания' }}</h3>
      <p v-if="!publicMode" class="text-3 muted">Создайте тест на основе готового конспекта.</p>
      <BaseButton v-if="!publicMode" :loading="loading" @click="generate">Создать тест</BaseButton>
    </div>
    <div v-else-if="publicMode && !result && !training" class="empty-state">
      <h3 class="title-4">Тренировка на время</h3>
      <p class="text-3 muted">Вопросов: {{ quiz.questions.length }}. Можно пройти прямо здесь, без копирования материала.</p>
      <p class="text-3 muted">Если закрыть или обновить страницу, тренировка прервётся. При возвращении нужно начать новую попытку.</p>
      <p class="text-3 muted">Ваше имя, процент и время попадут в рейтинг. Подробные ответы останутся видны только вам.</p>
      <BaseButton :loading="starting" @click="startTraining">Начать тренировку</BaseButton>
    </div>
    <template v-else-if="question">
      <p v-if="publicMode && training && !result" class="notice text-3" aria-live="off">Время тренировки: {{ formatTrainingTime(trainingElapsed) }}</p>
      <div v-if="viewingAttempt" class="notice text-3">
        <p>Попытка от {{ formatAttemptDate(viewingAttempt.created_at) }}. Ответы сохранены.</p>
        <BaseButton v-if="!savedPublicAttemptId" variant="transparent" @click="restart">К текущему тесту</BaseButton>
      </div>
      <div
        v-if="result"
        class="quiz-panel__score"
        :class="`quiz-panel__score--${scoreLevel.name}`"
        role="status"
      >
        <component :is="scoreLevel.icon" :size="40" aria-hidden="true" />
        <div>
          <h3 class="title-3">{{ scorePercent }}%</h3>
          <p class="text-2">{{ scoreLevel.label }}</p>
          <p class="text-3">
            Правильных ответов: {{ result.correct }} из {{ result.total }}.
            <template v-if="result.duration_ms != null">Время: {{ formatTrainingTime(result.duration_ms) }}.</template>
          </p>
        </div>
      </div>
      <nav class="quiz-panel__numbers" aria-label="Вопросы теста">
        <button
          v-for="(item, index) in quiz.questions"
          :key="item.id"
          class="quiz-panel__number text-3"
          :class="{
            'quiz-panel__number--active': current === index,
            'quiz-panel__number--answered': answered(item.id),
          }"
          :aria-current="current === index ? 'step' : undefined"
          @click="selectQuestion(index)"
        >
          {{ index + 1 }}
        </button>
      </nav>
      <p class="text-3 muted">
        Вопрос {{ current + 1 }} из {{ quiz.questions.length }} ·
        {{
          question.question_type === 'multiple'
            ? 'Выберите несколько ответов'
            : 'Выберите один ответ'
        }}
      </p>
      <h3 class="title-4">{{ question.text }}</h3>
      <fieldset class="quiz-panel__options" :disabled="!!result || submitting">
        <legend class="sr-only">Варианты ответа</legend>
        <label
          v-for="option in question.answers"
          :key="option.id"
          class="quiz-panel__option text-2"
          :class="{
            'quiz-panel__option--correct': questionResult?.correct_ids.includes(option.id),
            'quiz-panel__option--wrong':
              !!questionResult &&
              answers[question.id]?.includes(option.id) &&
              !questionResult.correct_ids.includes(option.id),
          }"
          ><input
            :type="question.question_type === 'multiple' ? 'checkbox' : 'radio'"
            :name="question.id"
            :checked="answers[question.id]?.includes(option.id)"
            @change="select(option.id, ($event.target as HTMLInputElement).checked)"
          />{{ option.text }}</label
        >
      </fieldset>
      <p v-if="questionResult?.explanation" class="notice text-2">
        {{ questionResult.explanation }}
      </p>
      <div class="quiz-panel__navigation">
        <BaseButton variant="transparent" :disabled="current === 0 || submitting" @click="selectQuestion(current - 1)">
          <template #icon-left><ArrowLeft /></template>Назад
        </BaseButton>
        <div class="quiz-panel__navigation-actions">
          <BaseButton v-if="!result" variant="transparent" :loading="submitting" @click="submit">Завершить тест</BaseButton>
          <BaseButton v-if="current < quiz.questions.length - 1" :disabled="submitting" @click="selectQuestion(current + 1)">
            Следующий вопрос<template #icon-right><ArrowRight /></template>
          </BaseButton>
          <BaseButton v-else-if="result && !savedPublicAttemptId" @click="restart">Пройти ещё раз</BaseButton>
        </div>
      </div>
    </template>
    <BaseButton v-if="publicQuizId && !hideRanking" variant="transparent" :aria-expanded="rankingVisible" @click="rankingVisible = !rankingVisible">{{ rankingVisible ? 'Скрыть рейтинг' : 'Рейтинг тренировок' }}</BaseButton>
    <QuizLeaderboard v-if="publicQuizId && rankingVisible && !hideRanking" :quiz-id="publicQuizId" :revision="rankingRevision" />
    <BaseButton v-if="!demo" variant="transparent" :aria-expanded="historyVisible" aria-controls="quiz-history" :disabled="submitting || historyOpening" @click="toggleHistory">
      {{ historyVisible ? 'Скрыть историю' : 'История прохождений' }}
    </BaseButton>
    <section v-if="!demo && historyVisible" id="quiz-history" class="quiz-panel__history" aria-labelledby="quiz-history-title">
      <div class="section-heading">
        <h3 id="quiz-history-title" class="title-4">История прохождений</h3>
        <button class="text-link text-3" :disabled="historyLoading || submitting || historyOpening" @click="loadHistory(true)">Обновить</button>
      </div>
      <p v-if="historyError" class="text-3 danger" role="alert">{{ historyError }}</p>
      <p v-if="historyLoading" class="text-3 muted" role="status">Загружаем историю…</p>
      <p v-else-if="!attempts.length && !historyError" class="text-3 muted">Пока нет завершённых попыток. После прохождения результат появится здесь.</p>
      <ul class="quiz-panel__attempts">
        <li v-for="attempt in attempts" :key="attempt.id">
          <button
            class="quiz-panel__attempt text-3"
            :class="{ 'quiz-panel__attempt--active': viewingAttempt?.id === attempt.id || result?.attempt_id === attempt.id }"
            :disabled="loading || submitting || historyOpening"
            @click="openAttempt(attempt)"
          >
            <span>{{ formatAttemptDate(attempt.created_at) }}</span>
            <strong>{{ Math.round(attempt.score * 100) }}% · {{ attempt.correct }} из {{ attempt.total }}<template v-if="attempt.duration_ms != null"> · {{ formatTrainingTime(attempt.duration_ms) }}</template></strong>
            <span>Посмотреть ответы</span>
          </button>
        </li>
      </ul>
      <BaseButton v-if="attempts.length < attemptsTotal" variant="transparent" :loading="historyLoading" @click="loadHistory()">Показать ещё</BaseButton>
    </section>
  </section>
</template>

<style scoped>
.quiz-panel__navigation, .quiz-panel__navigation-actions { display: flex; align-items: center; flex-wrap: wrap; gap: 16px; }
.quiz-panel__navigation { justify-content: space-between; }

.quiz-panel__history { border-top: 1px solid var(--color-panel-border); padding-top: 24px; display: flex; flex-direction: column; gap: 16px; }
.quiz-panel__attempts { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 10px; }
.quiz-panel__attempt { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px; width: 100%; padding: 16px; text-align: left; border-radius: var(--radius-card); border: 1px solid var(--color-panel-border); background: var(--color-background); color: var(--color-text-primary); }
.quiz-panel__attempt--active { border-color: var(--color-yellow); }
.quiz-panel__attempt:disabled { opacity: .65; }

.quiz-panel {
  display: flex;
  flex-direction: column;
  gap: 26px;
  padding: 32px;
  min-height: 600px;
}
.quiz-panel__heading {
  display: flex;
  align-items: center;
  gap: 24px;
}
.quiz-panel__heading svg {
  color: var(--color-yellow);
}
.quiz-panel__numbers {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}
.quiz-panel__number {
  width: 44px;
  height: 44px;
  border: 1px solid var(--color-panel-border);
  border-radius: var(--border-radius-sm);
  background: var(--color-background);
  color: var(--color-text-secondary);
}
.quiz-panel__number--answered {
  border-color: var(--color-green);
}
.quiz-panel__number--active {
  background: var(--color-yellow);
  color: var(--color-background);
}
.quiz-panel__options {
  display: flex;
  flex-direction: column;
  gap: 14px;
  border: 0;
  margin: 0;
  padding: 0;
}
.quiz-panel__option {
  display: flex;
  align-items: center;
  gap: 18px;
  min-height: 60px;
  padding: 14px 20px;
  border: 1px solid var(--color-panel-border);
  border-radius: var(--radius-card);
  cursor: pointer;
}
.quiz-panel__option input {
  appearance: none;
  flex-shrink: 0;
  display: grid;
  place-content: center;
  width: 22px;
  height: 22px;
  margin: 0;
  border: 1.5px solid var(--color-border);
  border-radius: 6px;
  background: transparent;
  cursor: pointer;
}
.quiz-panel__option input:focus-visible {
  outline: 2px solid var(--color-yellow);
  outline-offset: 2px;
}
.quiz-panel__option input[type='radio'] {
  border-radius: 50%;
}
.quiz-panel__option input:checked {
  border-color: var(--color-yellow);
  background: var(--color-yellow);
}
.quiz-panel__option input:checked::before {
  content: '';
  width: 12px;
  height: 12px;
  background: var(--color-dark);
  clip-path: polygon(14% 44%, 0 65%, 50% 100%, 100% 16%, 80% 0%, 43% 62%);
}
.quiz-panel__option input[type='radio']:checked::before {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  clip-path: none;
}
.quiz-panel__option--correct {
  border-color: var(--color-success);
  background: color-mix(in srgb, var(--color-green) 30%, transparent);
}
.quiz-panel__option--wrong {
  border-color: var(--color-danger);
  background: color-mix(in srgb, var(--color-danger) 18%, transparent);
}
.quiz-panel__option--correct input:checked {
  border-color: var(--color-success);
  background: var(--color-success);
}
.quiz-panel__option--wrong input:checked {
  border-color: var(--color-danger);
  background: var(--color-danger);
}
.quiz-panel__score {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 24px;
  border-radius: var(--border-radius-md);
  background: color-mix(in srgb, var(--score-color) 18%, var(--color-panel));
  border: 1px solid color-mix(in srgb, var(--score-color) 55%, transparent);
}
.quiz-panel__score > svg,
.quiz-panel__score h3 {
  color: var(--score-color);
}
.quiz-panel__score > svg {
  flex-shrink: 0;
}
.quiz-panel__score--low { --score-color: var(--color-danger); }
.quiz-panel__score--medium { --score-color: var(--color-yellow); }
.quiz-panel__score--high { --score-color: var(--color-success); }
@media (max-width: 768px) {
  .quiz-panel {
    padding: 20px 16px;
    min-height: 0;
  }
  .quiz-panel__heading,
  .quiz-panel__score {
    flex-wrap: wrap;
  }
  .quiz-panel__option {
    padding: 12px 14px;
    gap: 12px;
  }
}
</style>
