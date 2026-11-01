<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { ArrowLeft, ArrowRight, CheckCircle2, ClipboardList, RefreshCw } from 'lucide-vue-next'
import { useSessionStore } from '@/entities/session'
import {
  createMaterialApi,
  type Quiz,
  type QuizResult,
  type SubmittedAnswer,
} from '@/entities/material'
import { BaseButton } from '@/shared/ui/button'
const props = defineProps<{
  materialId: string
  demo?: Quiz
  demoAnswers?: Record<string, string[]>
  initialQuiz?: Quiz
  generationPending?: boolean
}>()
const api = createMaterialApi(useSessionStore().request)
const quiz = ref<Quiz | null>(null)
const current = ref(0)
const answers = ref<Record<string, string[]>>({})
const result = ref<QuizResult | null>(null)
const loading = ref(false)
const processing = ref(false)
const submitting = ref(false)
const error = ref('')
let timer: ReturnType<typeof setTimeout> | undefined
let controller = new AbortController()
let deadline = 0
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
  result.value = null
  answers.value = {}
  selectQuestion(0)
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
  if (signal.aborted) return
  clearTimeout(timer)
  error.value = ''
  loading.value = true
  try {
    const status = await api.quizStatus(props.materialId, signal)
    if (signal.aborted) return
    if (status.quiz_id && status.status === 'done') {
      quiz.value = await api.quiz(props.materialId, signal)
      processing.value = false
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
    if (!signal.aborted) loading.value = false
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
  if (!quiz.value || submitting.value) return
  const missing = quiz.value.questions.findIndex((item) => !answered(item.id))
  if (missing >= 0) {
    current.value = missing
    error.value = 'Ответьте на вопрос перед завершением теста.'
    return
  }
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
      const response = await api.submit(props.materialId, submitted)
      if (signal.aborted) return
      result.value = response
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
  () => props.materialId,
  () => {
    stop()
    controller = new AbortController()
    current.value = 0
    quiz.value = props.demo ?? props.initialQuiz ?? null
    result.value = null
    answers.value = {}
    processing.value = !!props.generationPending
    submitting.value = false
    deadline = Date.now() + 10 * 60 * 1000
    if (!props.demo && !props.initialQuiz) void load(controller.signal)
  },
  { immediate: true }
)
onBeforeUnmount(stop)
</script>

<template>
  <section class="surface quiz-panel" :aria-busy="loading || submitting">
    <header class="section-heading">
      <h2 class="title-3 quiz-panel__heading"><ClipboardList :size="38" />Тест</h2>
      <button
        v-if="!demo && !submitting"
        class="icon-button"
        :disabled="loading"
        aria-label="Обновить тест"
        @click="load(controller.signal)"
      >
        <RefreshCw />
      </button>
    </header>
    <p v-if="demo" class="notice text-3">Демонстрационный тест. Результат не сохраняется.</p>
    <p v-if="error" class="notice danger text-3" role="alert">{{ error }}</p>
    <div v-if="processing || (loading && !quiz)" class="empty-state" role="status">
      <ClipboardList :size="48" />
      <h3 class="title-4">
        {{ processing ? 'Создаём тест по вашему материалу' : 'Загружаем тест…' }}
      </h3>
      <p class="text-3 muted">Можно вернуться к конспекту. Генерация продолжится на сервере.</p>
    </div>
    <div v-else-if="!quiz || !quiz.questions.length" class="empty-state">
      <ClipboardList :size="48" />
      <h3 class="title-4">Проверьте свои знания</h3>
      <p class="text-3 muted">Создайте тест на основе готового конспекта.</p>
      <BaseButton :loading="loading" @click="generate">Создать тест</BaseButton>
    </div>
    <template v-else-if="question">
      <div v-if="result" class="quiz-panel__score">
        <CheckCircle2 :size="40" />
        <div>
          <h3 class="title-3">{{ Math.round(result.score * 100) }}%</h3>
          <p class="text-3">
            Правильных ответов: {{ result.correct }}. Отправлено вопросов: {{ result.total }}.
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
      <div class="section-heading">
        <BaseButton variant="transparent" :disabled="current === 0 || submitting" @click="current--"
          ><template #icon-left><ArrowLeft /></template>Назад</BaseButton
        ><BaseButton
          v-if="current < quiz.questions.length - 1"
          :disabled="submitting"
          @click="selectQuestion(current + 1)"
          >Следующий вопрос<template #icon-right><ArrowRight /></template></BaseButton
        ><BaseButton v-else-if="!result" :loading="submitting" @click="submit"
          >Завершить тест</BaseButton
        ><BaseButton v-else @click="restart">Пройти ещё раз</BaseButton>
      </div>
    </template>
  </section>
</template>

<style scoped>
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
  width: 22px;
  height: 22px;
  accent-color: var(--color-yellow);
  flex-shrink: 0;
}
.quiz-panel__option--correct {
  border-color: var(--color-success);
  background: color-mix(in srgb, var(--color-green) 30%, transparent);
}
.quiz-panel__score {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 24px;
  border-radius: var(--border-radius-md);
  background: var(--color-green);
}
</style>
