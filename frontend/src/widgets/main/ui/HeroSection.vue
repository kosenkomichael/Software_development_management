<script setup lang="ts">
import { BaseButton } from '@/shared/ui/button'
</script>

<template>
  <section class="hero">
    <div class="container">
      <div class="hero__content">
        <div class="hero__information">
          <h1 class="title-1 hero__title">
            Лекция превращается в знания
            <span class="hero__accent"> за несколько минут </span>
          </h1>

          <p class="text-3 hero__description">
            Загрузите учебный материал — мы выделим главное, создадим структурированный конспект и
            подготовим тест для самопроверки
          </p>

          <div class="hero__actions">
            <BaseButton variant="yellow" size="large">
              Загрузить материал

              <template #icon-right>
                <svg
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  aria-hidden="true"
                >
                  <path d="M5 12h14" />
                  <path d="m12 5 7 7-7 7" />
                </svg>
              </template>
            </BaseButton>

            <BaseButton variant="transparent" size="large"> Посмотреть возможности </BaseButton>
          </div>
        </div>

        <div class="hero__preview">
          <span>Материал → Конспект + Тест</span>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.hero {
  width: 100%;
  padding-block: 100px;
}

.hero__content {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 0.9fr);
  align-items: center;
  gap: 64px;
}

.hero__information {
  min-width: 0;
}

.hero__title {
  max-width: 650px;
}

.hero__accent {
  color: var(--color-yellow);
}

.hero__description {
  max-width: 500px;
  margin-top: 24px;

  color: var(--color-text-primary);
}

.hero__actions {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;

  margin-top: 32px;
}

.hero__preview {
  display: flex;
  align-items: center;
  justify-content: center;

  min-height: 340px;
  padding: 24px;

  border: 1px dashed var(--color-border);
  border-radius: var(--border-radius-lg);

  color: var(--color-text-secondary);
  text-align: center;
}
</style>
