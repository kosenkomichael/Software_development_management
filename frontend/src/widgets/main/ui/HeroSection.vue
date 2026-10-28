<script setup lang="ts">
import { ArrowRight } from 'lucide-vue-next'

import { BaseButton } from '@/shared/ui/button'

import GenerationFlow from './hero/GenerationFlow.vue'
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
                <ArrowRight :size="20" />
              </template>
            </BaseButton>

            <BaseButton variant="transparent" size="large"> Посмотреть возможности </BaseButton>
          </div>
        </div>

        <div class="hero__visual">
          <GenerationFlow />
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.hero {
  width: 100%;
  min-height: calc(100svh - 110px);
  padding-block: 64px 100px;
}
.hero__content {
  display: grid;
  grid-template-columns: minmax(0, 0.87fr) minmax(0, 1fr);
  align-items: start;
  gap: clamp(32px, 3.4vw, 64px);
}
.hero__information,
.hero__visual {
  min-width: 0;
}
.hero__visual {
  padding-top: 16px;
}
.hero__title {
  font-size: clamp(36px, 3.2vw, 60px);
  line-height: 1.22;
}
.hero__accent {
  color: var(--color-yellow);
}
.hero__description {
  margin-top: 40px;
  font-size: clamp(18px, 1.38vw, 26px);
  line-height: 1.35;
}
.hero__actions {
  display: flex;
  gap: 32px;
  margin-top: 48px;
}
.hero__actions :deep(.base-button) {
  flex: 1;
  min-width: 0;
  width: auto;
  padding-inline: 20px;
}
.hero__actions :deep(.base-button__icon svg) {
  width: 32px;
  height: 32px;
}
@media (max-width: 1400px) {
  .hero__actions {
    gap: 16px;
  }
  .hero__actions :deep(.base-button) {
    font-size: 16px;
  }
}
@media (max-width: 1100px) {
  .hero {
    padding-block: 48px 64px;
  }
  .hero__content {
    grid-template-columns: 1fr;
    gap: 48px;
  }
  .hero__information {
    max-width: 760px;
  }
  .hero__visual {
    width: 100%;
    max-width: 880px;
    margin-inline: auto;
    padding-top: 0;
  }
}
@media (max-width: 600px) {
  .hero__title {
    font-size: 36px;
  }
  .hero__description {
    margin-top: 24px;
  }
  .hero__actions {
    flex-direction: column;
    margin-top: 32px;
  }
  .hero__actions :deep(.base-button) {
    flex: auto;
    min-height: 60px;
    height: auto;
  }
}
</style>
