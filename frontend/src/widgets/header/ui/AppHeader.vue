<script setup lang="ts">
import { RouterLink } from 'vue-router'

import { BaseButton } from '@/shared/ui/button'
import logo from '@/shared/assets/images/logo.svg'
</script>

<template>
  <header class="header">
    <div class="container header__container">
      <RouterLink to="/" class="header__logo-link" aria-label="StudyAI — главная страница">
        <img :src="logo" alt="StudyAI" class="header__logo" />
      </RouterLink>

      <div class="header__actions">
        <BaseButton variant="transparent" size="small"> Войти </BaseButton>

        <BaseButton variant="yellow" size="small"> Зарегистрироваться </BaseButton>
      </div>
    </div>
  </header>
</template>

<style scoped>
.header {
  position: relative;
  z-index: 10;

  width: 100%;

  background-color: #0000001d;
}

.header__container {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 32px;
  min-height: 110px;
}

.header__logo-link {
  display: inline-flex;
  align-items: center;
  flex-shrink: 0;

  text-decoration: none;
}

.header__logo {
  display: block;
  width: auto;
  height: 55px;
}

.header__actions {
  display: flex;
  align-items: center;
  gap: 20px;
  flex-shrink: 0;
}

.header__actions :deep(.base-button--yellow) {
  min-width: 283px;
}
@media (max-width: 600px) {
  .header__container {
    min-height: 90px;
    gap: 16px;
    flex-wrap: wrap;
    padding-block: 16px;
  }
  .header__logo {
    height: 38px;
  }
  .header__actions {
    gap: 12px;
    flex-wrap: wrap;
  }
  .header__actions :deep(.base-button) {
    min-width: 0;
    min-height: 44px;
    font-size: 14px;
    padding-inline: 16px;
  }
}
</style>
