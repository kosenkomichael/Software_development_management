<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { ArrowRight, BookOpen } from 'lucide-vue-next'

import { LearningActivity } from '@/features/learning-activity'
import { useMaterialLibraryStore } from '@/features/material-library'
import { formatSize } from '@/entities/material'
import { BaseButton } from '@/shared/ui/button'

const library = useMaterialLibraryStore()
const router = useRouter()

const recent = computed(() => library.items.slice(0, 3))

onMounted(() => {
  void library.load()
})
</script>

<template>
  <div class="account-overview">
    <div v-if="library.error" class="notice text-3" role="alert">
      {{ library.error }}
      <button class="text-link" type="button" @click="library.load(true)">Повторить</button>
    </div>

    <section class="surface account-overview__continue">
      <header class="section-heading">
        <h2 class="title-4">Продолжить обучение</h2>
      </header>

      <p v-if="library.loading" class="text-3 muted" role="status">Загружаем библиотеку…</p>

      <p v-else-if="!recent.length" class="text-3 muted">
        Загрузите первую лекцию и начните обучение.
      </p>

      <div v-else class="account-overview__recent">
        <RouterLink
          v-for="item in recent"
          :key="item.id"
          :to="`/materials/${item.id}`"
          class="account-overview__recent-item text-3"
        >
          <BookOpen :size="22" />
          <span>{{ item.original_filename }}</span>
          <ArrowRight :size="20" />
        </RouterLink>
      </div>

      <BaseButton
        v-if="!recent.length && !library.loading"
        size="small"
        @click="router.push('/materials/new')"
      >
        Добавить материал
      </BaseButton>
    </section>

    <div class="account-overview__bottom">
      <section class="surface account-overview__storage">
        <header class="section-heading">
          <h2 class="title-4">Хранилище</h2>

          <button
            class="text-link text-4"
            type="button"
            disabled
            title="Увеличение лимита пока недоступно"
          >
            Увеличить лимит
            <ArrowRight :size="18" />
          </button>
        </header>

        <p class="text-3 muted">
          {{ library.loaded ? `Использовано ${formatSize(library.bytes)}` : 'Загружаем данные…' }}
        </p>

        <div class="account-overview__track" aria-hidden="true" />

        <p class="text-4 muted">Информация о лимите появится позже.</p>
      </section>

      <LearningActivity />
    </div>
  </div>
</template>

<style scoped>
.account-overview {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.account-overview__continue {
  display: flex;
  flex-direction: column;
  gap: 14px;

  min-height: 140px;
  padding: 18px 20px;
}

.account-overview__continue > :deep(.base-button) {
  align-self: flex-start;
}

.account-overview__recent {
  display: flex;
  gap: 12px;
}

.account-overview__recent-item {
  display: flex;
  align-items: center;
  flex: 1 1 0;
  gap: 12px;

  min-width: 0;
  padding: 12px 14px;

  border-radius: var(--radius-card);
  background: var(--color-background);
  color: var(--color-text-primary);
  text-decoration: none;
}

.account-overview__recent-item span {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.account-overview__recent-item svg {
  flex-shrink: 0;
  color: var(--color-yellow);
}

.account-overview__bottom {
  display: flex;
  gap: 16px;
}

.account-overview__bottom > * {
  display: flex;
  flex: 1 1 0;
  flex-direction: column;
  gap: 12px;

  min-width: 0;
  min-height: 145px;
  padding: 18px 20px;
}

.account-overview__track {
  width: 100%;
  max-width: 560px;
  height: 8px;

  border-radius: var(--border-radius-lg);
  background: var(--color-track);
}

@media (max-width: 768px) {
  .account-overview__continue {
    min-height: 0;
    gap: 12px;
    padding: 16px;
  }

  .account-overview__recent,
  .account-overview__bottom {
    flex-direction: column;
  }

  .account-overview__bottom > * {
    flex: 1 1 auto;
    padding: 16px;
  }
}
</style>
