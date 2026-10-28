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

  border-bottom: 1px solid var(--color-border);
}

.header__container {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 32px;
  background-color: #0000001d;

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
  gap: 12px;
  flex-shrink: 0;
}
</style>
