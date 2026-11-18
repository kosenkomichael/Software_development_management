<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { ArrowRight, BookOpen, CheckSquare } from 'lucide-vue-next'
import { useSessionStore } from '@/entities/session'
import { BaseButton } from '@/shared/ui/button'
interface Activity { is_public?: boolean; id: string; kind: 'upload' | 'attempt'; material_id: string; title: string; created_at: string; score: number | null }
const session = useSessionStore()
const items = ref<Activity[]>([])
const total = ref(0)
const page = ref(0)
const expanded = ref(false)
const loading = ref(false)
const error = ref('')
const controller = new AbortController()
const date = (value: string) => new Intl.DateTimeFormat('ru-RU', { day: 'numeric', month: 'long', hour: '2-digit', minute: '2-digit' }).format(new Date(value))
async function load(reset = false) {
  if (loading.value) return
  loading.value = true
  error.value = ''
  try {
    const next = reset ? 1 : page.value + 1
    const response = await session.request<{ items: Activity[]; total: number }>(`/auth/me/activity?page=${next}&page_size=5`, { signal: controller.signal })
    if (controller.signal.aborted) return
    items.value = reset ? response.items : [...items.value, ...response.items]
    total.value = response.total
    page.value = next
  } catch (reason) {
    if (!controller.signal.aborted) error.value = reason instanceof Error ? reason.message : 'Не удалось загрузить активность.'
  } finally { if (!controller.signal.aborted) loading.value = false }
}
function toggle() {
  expanded.value = !expanded.value
  if (expanded.value && items.value.length < total.value) void load()
  else if (!expanded.value) { items.value = items.value.slice(0, 5); page.value = 1 }
}
onMounted(() => void load(true))
onBeforeUnmount(() => controller.abort())
</script>
<template>
  <section class="surface learning-activity">
    <header class="section-heading">
      <h2 class="title-4">Недавняя активность</h2>
      <button v-if="total > 5" class="text-link text-4" :disabled="loading" :aria-expanded="expanded" @click="toggle">{{ expanded ? 'Свернуть' : 'Смотреть все' }} <ArrowRight :size="20" /></button>
    </header>
    <p v-if="error" class="text-3 danger" role="alert">{{ error }} <button class="text-link" @click="load(true)">Повторить</button></p>
    <p v-if="loading" class="text-3 muted" role="status">Загружаем активность…</p>
    <p v-else-if="!items.length && !error" class="text-3 muted">Здесь появятся загруженные материалы и результаты тестов.</p>
    <ul class="learning-activity__list">
      <li v-for="item in items" :key="`${item.kind}:${item.id}`">
        <RouterLink class="learning-activity__item" :to="item.is_public ? { name: 'public-attempt', params: { attemptId: item.id } } : { name: 'material', params: { id: item.material_id }, query: item.kind === 'attempt' ? { tab: 'quiz', attempt: item.id } : {} }">
          <component :is="item.kind === 'upload' ? BookOpen : CheckSquare" :size="24" class="accent" aria-hidden="true" />
          <div class="learning-activity__text">
            <span class="text-3">{{ item.kind === 'upload' ? 'Загружен материал' : 'Завершён тест' }}<template v-if="item.score !== null"> · {{ Math.round(item.score * 100) }}%</template></span>
            <span class="text-3 learning-activity__title">{{ item.title }}</span>
            <time class="text-4 muted" :datetime="item.created_at">{{ date(item.created_at) }}</time>
          </div>
          <ArrowRight :size="18" aria-hidden="true" />
        </RouterLink>
      </li>
    </ul>
    <BaseButton v-if="expanded && items.length < total" variant="transparent" :loading="loading" @click="load()">Показать ещё</BaseButton>
  </section>
</template>
<style scoped>
.learning-activity { padding: 28px; display: flex; flex-direction: column; gap: 20px; min-width: 0; }
.learning-activity__list { list-style: none; padding: 0; margin: 0; }
.learning-activity__item { display: flex; align-items: center; gap: 16px; padding: 16px 0; color: var(--color-text-primary); text-decoration: none; border-bottom: 1px solid var(--color-panel-border); }
.learning-activity__text { display: flex; flex-direction: column; gap: 6px; flex: 1; min-width: 0; }
.learning-activity__title { overflow-wrap: anywhere; }
.learning-activity__item > svg { flex-shrink: 0; }
</style>
