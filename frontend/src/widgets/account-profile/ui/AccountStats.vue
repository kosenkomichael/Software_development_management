<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { BarChart2, BookOpen, CheckSquare } from 'lucide-vue-next'
import { useSessionStore } from '@/entities/session'

interface AccountStatsData {
  materials_count: number
  attempts_count: number
  average_score: number | null
}

const session = useSessionStore()

const stats = ref<AccountStatsData | null>(null)
const loading = ref(false)
const error = ref('')

const controller = new AbortController()

const cards = computed(() => [
  {
    key: 'materials',
    title: 'Материалов',
    value: stats.value ? stats.value.materials_count : '…',
    description: 'в вашей библиотеке',
    icon: BookOpen,
  },
  {
    key: 'tests',
    title: 'Пройдено тестов',
    value: stats.value ? stats.value.attempts_count : '…',
    description: 'завершённых попыток',
    icon: CheckSquare,
  },
  {
    key: 'score',
    title: 'Средний результат',
    value: !stats.value
      ? '…'
      : stats.value.average_score === null
        ? '—'
        : `${Math.round(stats.value.average_score * 100)}%`,
    description: stats.value?.attempts_count ? 'по всем тестам' : 'пройдите первый тест',
    icon: BarChart2,
  },
])

async function loadStats() {
  if (loading.value) return

  loading.value = true
  error.value = ''

  try {
    const data = await session.request<AccountStatsData>('/auth/me/stats', {
      signal: controller.signal,
    })

    if (!controller.signal.aborted) {
      stats.value = data
    }
  } catch (reason) {
    if (!controller.signal.aborted) {
      error.value = reason instanceof Error ? reason.message : 'Не удалось загрузить статистику.'
    }
  } finally {
    if (!controller.signal.aborted) {
      loading.value = false
    }
  }
}

onMounted(() => {
  void loadStats()
})

onBeforeUnmount(() => {
  controller.abort()
})
</script>

<template>
  <section class="account-stats" aria-label="Статистика обучения" :aria-busy="loading">
    <p v-if="error" class="notice text-3" role="alert">
      {{ error }}
      <button class="text-link" type="button" @click="loadStats">Повторить</button>
    </p>

    <div class="account-stats__cards">
      <article
        v-for="card in cards"
        :key="card.key"
        class="surface account-stats__card"
        :class="`account-stats__card--${card.key}`"
      >
        <span class="account-stats__icon">
          <component :is="card.icon" :stroke-width="1.8" aria-hidden="true" />
        </span>

        <div class="account-stats__content">
          <strong class="title-4">{{ card.value }}</strong>
          <p class="text-3">{{ card.title }}</p>
          <p class="text-4 muted">{{ card.description }}</p>
        </div>
      </article>
    </div>
  </section>
</template>

<style scoped>
.account-stats {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.account-stats__cards {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

.account-stats__card {
  display: flex;
  align-items: center;
  flex: 1 1 300px;
  gap: 24px;

  min-width: 0;
  min-height: 120px;
  padding: 18px 24px;
}

.account-stats__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;

  width: 76px;
  height: 76px;

  border-radius: 20px;
  color: var(--color-white);
}

.account-stats__icon :deep(svg) {
  width: 40px;
  height: 40px;
}

.account-stats__card--materials .account-stats__icon {
  background-color: var(--color-green);
}

.account-stats__card--tests .account-stats__icon {
  background-color: var(--color-orange);
}

.account-stats__card--score .account-stats__icon {
  background-color: var(--color-blue);
}

.account-stats__content {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 3px;
  min-width: 0;
}

.account-stats__content strong {
  color: var(--color-text-primary);
  font-weight: var(--font-weight-semibold);
  line-height: 1.2;
}

.account-stats__content p {
  line-height: 1.3;
  overflow-wrap: anywhere;
}

@media (max-width: 768px) {
  .account-stats__card {
    flex-basis: 100%;
    min-height: 100px;
    gap: 16px;
    padding: 16px;
  }

  .account-stats__icon {
    width: 56px;
    height: 56px;
    border-radius: 16px;
  }

  .account-stats__icon :deep(svg) {
    width: 30px;
    height: 30px;
  }
}
</style>
