<script setup lang="ts">
import { BookOpen, ListChecks, Upload } from 'lucide-vue-next'

const steps = [
  {
    number: '01',
    title: 'Загрузите материал',
    description: 'Добавьте лекцию или учебный материал в формате PDF, DOCX или PPTX',
    icon: Upload,
    type: 'upload',
  },
  {
    number: '02',
    title: 'Получите конспект',
    description: 'Система выделит определения, основные тезисы и важные факты',
    icon: BookOpen,
    type: 'summary',
  },
  {
    number: '03',
    title: 'Проверьте знания',
    description: 'Пройдите автоматически созданный тест и посмотрите результаты',
    icon: ListChecks,
    type: 'test',
  },
]
</script>

<template>
  <section id="how-it-works" class="how-it-works">
    <h2 class="title-2">Как это работает?</h2>

    <div class="how-it-works__steps">
      <article
        v-for="step in steps"
        :key="step.number"
        class="surface how-it-works__step"
        :class="`how-it-works__step--${step.type}`"
      >
        <div class="how-it-works__header">
          <span class="how-it-works__icon">
            <component :is="step.icon" :size="40" :stroke-width="1.8" aria-hidden="true" />
          </span>

          <span class="title-3 accent">
            {{ step.number }}
          </span>
        </div>

        <div class="how-it-works__content">
          <h3 class="text-1">{{ step.title }}</h3>
          <p class="text-2 muted">{{ step.description }}</p>
        </div>
      </article>
    </div>
  </section>
</template>

<style scoped>
.how-it-works {
  scroll-margin-top: calc(var(--header-height) + 32px);
}

.how-it-works__steps {
  display: flex;
  gap: 28px;
  margin-top: 40px;
}

.how-it-works__step {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 32px;

  min-width: 0;
  min-height: 260px;
  padding: 32px;

  border-radius: var(--radius-panel);
}

.how-it-works__header {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 20px;
}

.how-it-works__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;

  width: 76px;
  height: 76px;

  border-radius: 20px;
  background-color: var(--step-color);
  color: var(--color-white);
}

.how-it-works__step--upload {
  --step-color: var(--color-blue);
}

.how-it-works__step--summary {
  --step-color: var(--color-green);
}

.how-it-works__step--test {
  --step-color: var(--color-orange);
}

.how-it-works__content {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.how-it-works__content p {
  line-height: 1.4;
}

@media (max-width: 1023px) {
  .how-it-works__steps {
    flex-direction: column;
  }

  .how-it-works__step {
    min-height: 0;
  }
}

@media (max-width: 768px) {
  .how-it-works__step {
    gap: 24px;
    padding: 24px;
  }

  .how-it-works__icon {
    width: 64px;
    height: 64px;
    border-radius: 16px;
  }
}
</style>
