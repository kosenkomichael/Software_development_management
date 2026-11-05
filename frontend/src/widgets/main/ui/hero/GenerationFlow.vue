<script setup lang="ts">
import { designAssets } from '@/shared/assets'
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
      <img
        :src="designAssets.arrowLeft"
        alt=""
        class="generation-flow__arrow generation-flow__arrow--left"
      /><img
        :src="designAssets.arrowRight"
        alt=""
        class="generation-flow__arrow generation-flow__arrow--right"
      /><img :src="designAssets.sourcePlus" alt="" class="generation-flow__plus" />
    </div>
    <div class="generation-flow__results">
      <ResultCard
        variant="summary"
        title="Конспект готов"
        :items="summaryItems"
        button-text="Открыть конспект"
      /><ResultCard
        variant="test"
        title="Тест готов"
        :items="testItems"
        button-text="Начать тест"
      />
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
.generation-flow__arrow {
  position: absolute;
  top: 18px;
  max-width: none;
}
.generation-flow__arrow--left {
  left: calc(50% - 282px);
  transform: rotate(167.84deg);
}
.generation-flow__arrow--right {
  left: calc(50% + 34px);
  transform: rotate(12.16deg) scaleY(-1);
}
.generation-flow__plus {
  position: absolute;
  left: calc(50% - 34px);
  top: -19px;
}
.generation-flow__results {
  display: flex;
  gap: clamp(20px, 2.8vw, 52px);
}
.generation-flow__results > * {
  flex: 1;
  min-width: 0;
}
@media (max-width: 768px) {
  .generation-flow__source {
    width: 100%;
  }
  .generation-flow__connector {
    display: none;
  }
  .generation-flow__results {
    flex-direction: column;
  }
}
</style>
