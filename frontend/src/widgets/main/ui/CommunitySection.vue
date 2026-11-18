<script setup lang="ts">
import { ArrowRight } from 'lucide-vue-next'
import { useRouter } from 'vue-router'
import { StudyMaterialCard, type Material } from '@/entities/material'

const router = useRouter()

const examples: Material[] = [
  'Основы нейронных сетей',
  'Функции активации',
  'Обучение нейронной сети',
].map((name, index) => ({
  id: `example-${index}`,
  original_filename: name,
  content_type: 'application/pdf',
  size_bytes: 12 * 1024 * 1024,
  status: 'done',
  created_at: '',
}))
</script>

<template>
  <section class="community">
    <header class="community__header">
      <div class="community__information">
        <h2 class="title-2">Учись вместе с другими</h2>
        <p class="text-2 muted">Изучай готовые конспекты и проверяй знания с помощью тестов</p>
      </div>

      <RouterLink to="/community" class="community__link">
        Все материалы
        <ArrowRight :size="22" />
      </RouterLink>
    </header>

    <div class="community__examples">
      <StudyMaterialCard
        v-for="item in examples"
        :key="item.id"
        :material="item"
        demo
        author="Пример материала"
        @open="router.push('/community')"
        @quiz="router.push('/community')"
        @details="router.push('/community')"
      />
    </div>
  </section>
</template>

<style scoped>
.community__header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 32px;
}

.community__information {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.community__link {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;

  padding-bottom: 6px;

  color: var(--color-yellow);
  font-size: var(--font-size-text-2);
  text-decoration: none;

  transition: color var(--transition-default);
}

.community__link:hover {
  color: var(--color-white);
}

.community__examples {
  display: flex;
  align-items: stretch;
  gap: 28px;
  margin-top: 40px;
}

.community__examples > * {
  flex: 1 1 0;
  min-width: 0;
}

.community__examples :deep(.study-card__pill--notes) {
  background-color: var(--color-green);
}

.community__examples :deep(.study-card__pill--quiz) {
  background-color: var(--color-orange);
}

@media (max-width: 1100px) {
  .community__examples {
    flex-wrap: wrap;
  }

  .community__examples > * {
    flex: 1 1 calc(50% - 14px);
  }
}

@media (max-width: 768px) {
  .community__header {
    flex-direction: column;
    align-items: flex-start;
    gap: 20px;
  }

  .community__examples {
    gap: 20px;
    margin-top: 32px;
  }

  .community__examples > * {
    flex-basis: 100%;
  }
}
</style>
