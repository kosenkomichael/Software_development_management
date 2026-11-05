<script setup lang="ts">
import { ArrowRight } from 'lucide-vue-next'
import { useRouter } from 'vue-router'
import { designAssets } from '@/shared/assets'

import { BaseButton } from '@/shared/ui/button'

import GenerationFlow from './hero/GenerationFlow.vue'
const router = useRouter()
</script>

<template>
  <section class="hero" :style="{ backgroundImage: `url(${designAssets.heroBackground})` }">
    <div class="container">
      <div class="hero__content">
        <div class="hero__information">
          <h1 class="title-1 hero__title">
            Лекция превращается в знания
            <span class="hero__accent"> за несколько минут </span>
          </h1>

          <p class="text-1 hero__description">
            Загрузите учебный материал — мы выделим главное, создадим структурированный конспект и
            подготовим тест для самопроверки
          </p>

          <div class="hero__actions">
            <BaseButton variant="yellow" size="large" @click="router.push('/materials/new')">
              Загрузить материал

              <template #icon-right>
                <ArrowRight :size="20" />
              </template>
            </BaseButton>

            <BaseButton
              variant="transparent"
              size="large"
              @click="router.push({ path: '/', hash: '#how-it-works' })"
            >
              Посмотреть возможности
            </BaseButton>
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
  position: relative;
  isolation: isolate;
  width: 100%;
  min-height: 884px;
  padding-block: calc(110px + 58px) 140px;
  background-size: 119.47% 141.56%;
  background-position: right top -172px;
  background-repeat: no-repeat;
}
.hero::after {
  content: '';
  position: absolute;
  inset: auto 0 0;
  height: 240px;
  background: linear-gradient(
    to bottom,
    transparent,
    color-mix(in srgb, var(--color-background) 50%, transparent) 50%,
    var(--color-background)
  );
  pointer-events: none;
  z-index: -1;
}
.hero__content {
  display: flex;
  align-items: start;
  gap: clamp(32px, 3.4vw, 64px);
}
.hero__information,
.hero__visual {
  min-width: 0;
  flex: 1;
}
.hero__visual {
  padding-top: 16px;
  margin-right: 44px;
}
.hero__information {
  flex: 0.87;
}
.hero__title {
  font-size: var(--font-size-title-1);
  line-height: 1.22;
  font-weight: var(--font-weight-semibold);
}
.hero__accent {
  color: var(--color-yellow);
}
.hero__description {
  margin-top: 40px;
  line-height: 1.4;
}
.hero__actions {
  display: flex;
  gap: 30px;
  margin-top: 48px;
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
    padding-block: calc(110px + 48px) 64px;
  }
  .hero__content {
    flex-direction: column;
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
@media (max-width: 768px) {
  .hero {
    padding-top: calc(142px + 48px);
    min-height: 0;
    background-size: cover;
    background-position: center top;
  }
  .hero::after {
    height: 120px;
  }
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
  .hero__visual {
    margin-right: 0;
  }
  .hero__actions :deep(.base-button) {
    flex: auto;
    min-height: 60px;
    height: auto;
  }
}
</style>
