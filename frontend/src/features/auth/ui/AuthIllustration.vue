<script setup lang="ts">
import authIllustration from '@/shared/assets/images/auth-figma.png'
</script>

<template>
  <aside
    class="auth-illustration"
    :style="{ '--auth-illustration-image': `url(${authIllustration})` }"
  >
    <h2 class="title-2 auth-illustration__title">
      Конспекты<br />и тесты<br /><span>из лекций</span>
    </h2>
    <p class="text-2 auth-illustration__description">
      Загружайте учебные материалы, получайте краткие конспекты и тесты для самопроверки.<br />Экономьте
      время и учитесь с удовольствием.
    </p>
  </aside>
</template>

<style scoped>
.auth-illustration {
  display: flex;
  flex-direction: column;
  flex: 0 0 50%;
  position: relative;
  isolation: isolate;
  overflow: hidden;
  padding: 35px 26px 32px 48px;
  border-radius: 30px;
  background-color: var(--color-auth-surface);
}
.auth-illustration::before {
  content: '';
  position: absolute;
  inset: 0;
  z-index: -1;
  background-image: var(--auth-illustration-image);
  background-size: 106.99% 107.17%;
  background-position: left -24.35px top 0.65px;
  background-repeat: no-repeat;
  opacity: 0.8;
}
.auth-illustration__title {
  line-height: 1;
  font-weight: var(--font-weight-semibold);
}
.auth-illustration__title span {
  color: var(--color-yellow);
}
.auth-illustration__description {
  margin-top: 12px;
  color: var(--color-text-secondary);
}
</style>
