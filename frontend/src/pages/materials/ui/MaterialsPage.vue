<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { FilePlus, LayoutGrid, List, RefreshCw } from 'lucide-vue-next'
import { useMaterialLibraryStore } from '@/features/material-library'
import { StudyMaterialCard, materialStatusLabel, type Material } from '@/entities/material'
import { BaseButton } from '@/shared/ui/button'
import { BaseModal } from '@/shared/ui/modal'
import { designAssets } from '@/shared/assets'
const router = useRouter()
const library = useMaterialLibraryStore()
const filter = ref('all')
const order = ref('new')
const view = ref('cards')
const selected = ref<Material | null>(null)
function openSelected() {
  if (!selected.value) return
  open(selected.value)
  selected.value = null
}
const filters = computed(() => [
  { id: 'all', label: 'Все', count: library.total },
  {
    id: 'notes',
    label: 'Конспекты',
    count: library.items.filter((item) => item.status === 'done').length,
  },
  { id: 'quiz', label: 'Тесты', count: Object.values(library.quizReady).filter(Boolean).length },
  { id: 'files', label: 'Лекции', count: library.total },
])
const visible = computed(() =>
  library.items
    .filter((item) =>
      filter.value === 'notes'
        ? item.status === 'done'
        : filter.value === 'quiz'
          ? library.quizReady[item.id]
          : true
    )
    .slice()
    .sort((a, b) =>
      order.value === 'name'
        ? a.original_filename.localeCompare(b.original_filename, 'ru')
        : (order.value === 'old' ? 1 : -1) * (Date.parse(a.created_at) - Date.parse(b.created_at))
    )
)
async function refresh() {
  await library.load(true)
  await library.loadQuizStatuses()
}
onMounted(async () => {
  await library.load()
  await library.loadQuizStatuses()
})
function open(item: Material, tab?: string) {
  void router.push({ name: 'material', params: { id: item.id }, query: tab ? { tab } : {} })
}
</script>

<template>
  <div class="workspace-page materials-page">
    <header class="materials-page__header">
      <div class="page-heading">
        <h1 class="title-1">Мои материалы</h1>
        <p class="text-1 muted">Все загруженные лекции, конспекты и тесты в одном месте</p>
      </div>
      <div
        class="materials-page__quantity"
        :style="{ backgroundImage: `url(${designAssets.quotaTrack})` }"
      >
        <strong class="text-2">{{ library.total }}</strong
        ><span class="text-4 muted">Материалов</span>
      </div>
    </header>
    <div class="materials-page__toolbar">
      <div class="materials-page__filters" aria-label="Тип материала">
        <button
          v-for="tab in filters"
          :key="tab.id"
          class="surface materials-page__filter text-3"
          :class="{ 'materials-page__filter--active': filter === tab.id }"
          type="button"
          :aria-pressed="filter === tab.id"
          @click="filter = tab.id"
        >
          {{ tab.label }} <span class="materials-page__count">{{ tab.count }}</span>
        </button>
      </div>
      <div class="materials-page__controls">
        <select v-model="order" class="app-input text-3" aria-label="Порядок сортировки">
          <option value="new">Сначала новые</option>
          <option value="old">Сначала старые</option>
          <option value="name">По названию</option>
        </select>
        <div class="surface materials-page__views">
          <button
            class="icon-button"
            :class="{ accent: view === 'cards' }"
            aria-label="Карточки"
            :aria-pressed="view === 'cards'"
            @click="view = 'cards'"
          >
            <LayoutGrid /></button
          ><button
            class="icon-button"
            :class="{ accent: view === 'list' }"
            aria-label="Список"
            :aria-pressed="view === 'list'"
            @click="view = 'list'"
          >
            <List />
          </button>
        </div>
        <button
          class="icon-button"
          type="button"
          aria-label="Обновить материалы"
          :disabled="library.loading"
          @click="refresh"
        >
          <RefreshCw />
        </button>
      </div>
    </div>
    <div v-if="library.error" class="notice text-3" role="alert">
      {{ library.error }} <button class="text-link" @click="refresh">Повторить</button>
    </div>
    <p v-if="library.loading" class="notice text-3" role="status">Загружаем материалы…</p>
    <div v-else-if="!visible.length && !library.error" class="surface empty-state">
      <FilePlus :size="48" />
      <h2 class="title-4">
        {{
          filter === 'all' || filter === 'files'
            ? 'Здесь будут ваши материалы'
            : 'Таких материалов пока нет'
        }}
      </h2>
      <p class="text-3 muted">
        Загрузите первую лекцию, чтобы получить конспект и проверить знания.
      </p>
      <BaseButton @click="router.push('/materials/new')">Добавить материал</BaseButton>
    </div>
    <div
      v-else
      class="materials-page__cards"
      :class="{ 'materials-page__cards--list': view === 'list' }"
    >
      <StudyMaterialCard
        v-for="item in visible"
        :key="item.id"
        :material="item"
        :quiz-ready="library.quizReady[item.id]"
        @open="open(item)"
        @quiz="open(item, 'quiz')"
        @details="selected = item"
      />
    </div>
    <BaseModal :open="!!selected" labelledby="material-info-title" @close="selected = null"
      ><div v-if="selected" class="materials-page__details">
        <h2 id="material-info-title" class="title-4">{{ selected.original_filename }}</h2>
        <p class="text-3 muted">
          {{ materialStatusLabel[selected.status] }} ·
          {{ new Date(selected.created_at).toLocaleDateString('ru-RU') }}
        </p>
        <p class="text-3 muted">Переименование, удаление и избранное станут доступны позже.</p>
        <BaseButton @click="openSelected">Открыть материал</BaseButton>
      </div></BaseModal
    >
  </div>
</template>

<style scoped>
.materials-page__header {
  display: flex;
  justify-content: space-between;
  gap: 24px;
}
.materials-page__header .page-heading {
  margin: 0;
}
.materials-page__quantity {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 152px;
  height: 152px;
  background-size: contain;
  background-repeat: no-repeat;
}
.materials-page__toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 24px;
}
.materials-page__filters,
.materials-page__controls,
.materials-page__views {
  display: flex;
  align-items: center;
  gap: 12px;
}
.materials-page__filter {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  min-height: 58px;
  color: var(--color-text-secondary);
  border-radius: var(--radius-card);
}
.materials-page__filter--active {
  background: var(--color-yellow);
  color: var(--color-background);
  border-color: var(--color-yellow);
}
.materials-page__count {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 29px;
  height: 29px;
  border-radius: 50%;
  background: var(--color-auth-input);
  color: var(--color-text-secondary);
  font-size: var(--font-size-text-4);
}
.materials-page__controls select {
  width: 220px;
  background: var(--color-panel);
}
.materials-page__views {
  gap: 0;
  padding: 6px;
  border-radius: var(--radius-card);
}
.materials-page__cards {
  display: flex;
  flex-wrap: wrap;
  gap: 26px;
  margin-top: 56px;
}
.materials-page__cards > * {
  flex: 0 0 calc((100% - 52px) / 3);
}
.materials-page__cards--list {
  flex-direction: column;
}
.materials-page__cards--list > * {
  flex-basis: auto;
}
.materials-page__details {
  display: flex;
  flex-direction: column;
  gap: 24px;
  width: 580px;
  padding: 40px;
}
</style>
