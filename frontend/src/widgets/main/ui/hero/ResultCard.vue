<script setup lang="ts">
import { ArrowRight, BookOpen, Check, ClipboardList } from 'lucide-vue-next'

import { BaseButton } from '@/shared/ui/button'

type ResultVariant = 'summary' | 'test'

interface Props {
  variant: ResultVariant
  title: string
  items: string[]
  buttonText: string
}

defineProps<Props>()
</script>

<template>
  <article class="result-card" :class="`result-card--${variant}`">
    <div class="result-card__header">
      <div class="result-card__icon">
        <BookOpen v-if="variant === 'summary'" :size="26" :stroke-width="1.8" aria-hidden="true" />

        <ClipboardList v-else :size="26" :stroke-width="1.8" aria-hidden="true" />
      </div>

      <h3 class="result-card__title">
        {{ title }}
      </h3>
    </div>

    <ul class="result-card__list">
      <li v-for="item in items" :key="item" class="result-card__item">
        <Check :size="17" :stroke-width="2" class="result-card__check" aria-hidden="true" />

        <span>{{ item }}</span>
      </li>
    </ul>

    <BaseButton
      :variant="variant === 'summary' ? 'transparent' : 'yellow'"
      size="small"
      full-width
      class="result-card__button"
      disabled
    >
      {{ buttonText }}

      <template #icon-right>
        <ArrowRight :size="18" />
      </template>
    </BaseButton>
  </article>
</template>

<style scoped>
.result-card {
  display: flex;
  flex-direction: column;
  min-width: 0;
  min-height: 357px;
  padding: 34px 32px 22px;
  background-color: var(--color-glass);
  border: 2px solid var(--color-glass-border);
  border-radius: 30px;
  backdrop-filter: blur(12px);
}
.result-card__header {
  display: flex;
  align-items: center;
  gap: 24px;
}
.result-card__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 76px;
  height: 76px;
  border-radius: 20px;
  color: var(--color-white);
}
.result-card__icon :deep(svg) {
  width: 44px;
  height: 44px;
}
.result-card--summary .result-card__icon {
  background-color: var(--color-green);
}
.result-card--test .result-card__icon {
  background-color: var(--color-orange);
}
.result-card__title {
  font-size: var(--font-size-text-1);
  line-height: 1.3;
  color: var(--color-text-primary);
}
.result-card__list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin: 16px 0 36px;
  padding: 0 0 0 52px;
  list-style: none;
}
.result-card__item {
  display: flex;
  align-items: flex-start;
  gap: 18px;
  font-size: var(--font-size-text-2);
  line-height: 1.4;
  color: var(--color-text-secondary);
}
.result-card__check {
  flex-shrink: 0;
  width: 28px;
  height: 28px;
  color: var(--color-white);
}
.result-card__button {
  margin-top: auto;
  min-width: 0;
  min-height: 68px;
  padding-inline: 16px;
}
.result-card__button :deep(.base-button__icon svg) {
  width: 30px;
  height: 30px;
}
.result-card .result-card__button:disabled {
  opacity: 1;
  cursor: default;
}
@media (max-width: 1600px) {
  .result-card {
    padding: 24px 20px;
  }
  .result-card__header {
    gap: 16px;
  }
  .result-card__icon {
    width: 56px;
    height: 56px;
    border-radius: 16px;
  }
  .result-card__icon :deep(svg) {
    width: 34px;
    height: 34px;
  }
  .result-card__title {
    font-size: 20px;
  }
  .result-card__list {
    padding-left: 12px;
  }
  .result-card__item {
    gap: 12px;
    font-size: 16px;
  }
  .result-card__button {
    font-size: 16px;
  }
}
@media (max-width: 600px) {
  .result-card {
    min-height: 300px;
  }
}
@media (max-width: 768px) {
  .result-card {
    min-height: 0;
    padding: 20px 16px;
  }
  .result-card__header {
    gap: 12px;
  }
  .result-card__icon {
    width: 48px;
    height: 48px;
  }
  .result-card__icon :deep(svg) {
    width: 28px;
    height: 28px;
  }
  .result-card__button {
    min-height: 56px;
  }
}
</style>
