<script setup lang="ts">
import { Plus } from 'lucide-vue-next'

import MaterialCard from './MaterialCard.vue'
import ResultCard from './ResultCard.vue'

const summaryItems = ['Основные тезисы', 'Ключевые понятия', 'Чёткая структура']

const testItems = ['15 вопросов', 'Разные типы заданий', 'Проверка знаний']
</script>

<template>
  <div class="generation-flow">
    <div class="generation-flow__source">
      <MaterialCard file-name="Машинное обучение.pdf" :pages="28" file-size="12 МБ" />
    </div>

    <div class="generation-flow__connector" aria-hidden="true">
      <svg
        class="generation-flow__lines"
        viewBox="0 0 520 44"
        preserveAspectRatio="none"
        fill="none"
      >
        <path d="M260 8 C260 24 123 3 123 43" stroke="currentColor" stroke-width="1.2" />

        <path d="M260 8 C260 24 397 3 397 43" stroke="currentColor" stroke-width="1.2" />

        <path
          d="M117 36 L123 43 L129 36"
          stroke="currentColor"
          stroke-width="1.2"
          stroke-linecap="round"
          stroke-linejoin="round"
        />

        <path
          d="M391 36 L397 43 L403 36"
          stroke="currentColor"
          stroke-width="1.2"
          stroke-linecap="round"
          stroke-linejoin="round"
        />
      </svg>

      <div class="generation-flow__plus">
        <Plus :size="24" :stroke-width="1.8" />
      </div>
    </div>

    <div class="generation-flow__results">
      <ResultCard
        variant="summary"
        title="Конспект готов"
        :items="summaryItems"
        button-text="Открыть конспект"
      />

      <ResultCard variant="test" title="Тест готов" :items="testItems" button-text="Начать тест" />
    </div>
  </div>
</template>

<style scoped>
.generation-flow {
  width: 100%;
}
.generation-flow__source {
  width: 53%;
  margin-inline: auto;
}
.generation-flow__connector {
  position: relative;
  height: 68px;
}
.generation-flow__lines {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  color: var(--color-white);
  overflow: visible;
}
.generation-flow__plus {
  position: absolute;
  z-index: 1;
  top: 15px;
  left: 50%;
  display: grid;
  place-items: center;
  width: 68px;
  height: 68px;
  background-color: var(--color-yellow);
  color: var(--color-background);
  border-radius: 50%;
  transform: translate(-50%, -50%);
}
.generation-flow__plus :deep(svg) {
  width: 36px;
  height: 36px;
}
.generation-flow__results {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: clamp(20px, 2.8vw, 52px);
}
@media (max-width: 1400px) {
  .generation-flow__source {
    width: 65%;
  }
  .generation-flow__plus {
    width: 52px;
    height: 52px;
  }
}
@media (max-width: 600px) {
  .generation-flow__source {
    width: 100%;
  }
  .generation-flow__results {
    grid-template-columns: 1fr;
    gap: 20px;
  }
  .generation-flow__lines {
    display: none;
  }
  .generation-flow__connector {
    height: 56px;
  }
}
</style>
