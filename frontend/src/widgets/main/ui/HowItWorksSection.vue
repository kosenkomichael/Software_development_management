<script setup lang="ts">
import { BookOpen, ListChecks, Upload } from 'lucide-vue-next'

const steps = [
  { number: '01', title: 'Загрузите материал', description: 'PDF, DOCX, PPTX', icon: Upload },
  {
    number: '02',
    title: 'Получите конспект',
    icon: BookOpen,
    description: 'Система выделит определения, основные тезисы и важные факты',
  },
  {
    number: '03',
    title: 'Проверьте знания',
    icon: ListChecks,
    description: 'Пройдите автоматически созданный тест и посмотрите результаты',
  },
]
</script>

<template>
  <section id="how-it-works" class="how-it-works__how">
    <h2 class="title-1">Как это работает?</h2>
    <div class="how-it-works__steps">
      <article v-for="step in steps" :key="step.number" class="surface how-it-works__step">
        <span class="how-it-works__step-icon"
          ><component :is="step.icon" :size="50" aria-hidden="true"
        /></span>
        <div>
          <p class="title-3 accent">{{ step.number }}</p>
          <h3 class="text-1">{{ step.title }}</h3>
          <p class="text-2 muted">{{ step.description }}</p>
        </div>
      </article>
    </div>
  </section>
</template>

<style scoped>
.how-it-works__how {
  scroll-margin-top: calc(var(--header-height) + 32px);
}
.how-it-works__steps {
  display: flex;
  gap: 28px;
  margin-top: 40px;
}
.how-it-works__step {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  gap: 36px;
  flex: 1;
  min-width: 0;
  min-height: 263px;
  padding: 28px 32px;
  border-radius: var(--radius-panel);
}
.how-it-works__step > div {
  flex: 1 1 160px;
  min-width: 0;
  max-width: 100%;
  overflow-wrap: anywhere;
}
.how-it-works__step-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 104px;
  height: 104px;
  border-radius: 50%;
  background-color: color-mix(in srgb, var(--color-orange) 50%, var(--color-panel));
  color: var(--color-text-primary);
}
.how-it-works__step h3 {
  margin: 18px 0 14px;
}
.how-it-works__step .text-2 {
  line-height: 1.25;
}
@media (max-width: 1023px) {
  .how-it-works__steps {
    flex-direction: column;
  }
}
@media (max-width: 768px) {
  .how-it-works__step {
    flex-direction: column;
    gap: 16px;
    min-height: 0;
    padding: 20px;
  }
  .how-it-works__step-icon {
    width: 72px;
    height: 72px;
  }
  .how-it-works__step > div {
    flex-basis: auto;
  }
}
</style>
