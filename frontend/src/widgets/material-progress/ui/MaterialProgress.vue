<script setup lang="ts">
import { designAssets } from '@/shared/assets'
defineProps<{ step: 1 | 2 | 3; compact?: boolean }>()
const steps = ['Загрузка', 'Обработка', 'Результат']
</script>
<template>
  <ol
    class="material-progress"
    :class="{ 'material-progress--compact': compact }"
    aria-label="Создание материала"
  >
    <li
      v-for="(label, index) in steps"
      :key="label"
      :aria-current="step === index + 1 ? 'step' : undefined"
    >
      <span
        class="material-progress__number title-4"
        :class="{ 'material-progress__number--active': step === index + 1 }"
        :style="step !== index + 1 ? { backgroundImage: `url(${designAssets.stepInactive})` } : undefined"
        >{{ index + 1 }}</span
      ><span class="text-1" :class="{ accent: step === index + 1 }">{{ label }}</span
      ><img
        v-if="index < 2"
        :src="index === 0 ? designAssets.stepLineOne : designAssets.stepLineTwo"
        alt=""
      />
    </li>
  </ol>
</template>
<style scoped>
.material-progress {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 0;
  margin: 16px 0 8px;
  list-style: none;
}
.material-progress li {
  display: flex;
  align-items: center;
  gap: 16px;
}
.material-progress__number {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 81px;
  height: 81px;
  background-size: contain;
  background-repeat: no-repeat;
  background-position: center;
}
.material-progress__number--active {
  background-color: var(--color-yellow);
  border-radius: 50%;
  color: var(--color-panel);
}
.material-progress img {
  flex-shrink: 1;
  max-width: 100px;
}
.material-progress--compact {
  width: fit-content;
  align-self: flex-start;
  gap: 12px;
  margin: 12px 0 16px;
}
.material-progress--compact li {
  flex: 0 0 auto;
  gap: 12px;
  min-width: 0;
}
.material-progress--compact li:last-child {
  flex: 0 0 auto;
}
.material-progress--compact .material-progress__number {
  width: 60px;
  height: 60px;
  font-size: var(--font-size-text-1);
}
.material-progress--compact .material-progress__number--active {
  box-shadow: 0 0 24px color-mix(in srgb, var(--color-yellow) 18%, transparent);
  border-radius: 50%;
}
.material-progress--compact .text-1 {
  font-size: var(--font-size-text-2);
}
.material-progress--compact img {
  flex: 0 0 88px;
  width: 88px;
  max-width: 88px;
  margin-inline: 0;
  opacity: 0.35;
}
@media (max-width: 1100px) {
  .material-progress,
  .material-progress--compact {
    width: 100%;
  }
  .material-progress img {
    display: none;
  }
}
@media (max-width: 768px) {
  .material-progress {
    gap: 12px;
    justify-content: space-between;
    flex-wrap: wrap;
  }
  .material-progress li {
    gap: 8px;
  }
  .material-progress__number {
    width: 48px;
    height: 48px;
  }
  .material-progress--compact .material-progress__number {
    width: 40px;
    height: 40px;
  }
  .material-progress .text-1 {
    font-size: var(--font-size-text-3);
  }
}
</style>
