<script setup lang="ts">
import { RouterLink } from 'vue-router'
import { CircleUserRound } from 'lucide-vue-next'
import { useAuthModalStore } from '@/features/auth'
import { useSessionStore } from '@/entities/session'

import { BaseButton } from '@/shared/ui/button'
import logo from '@/shared/assets/images/logo.svg'

const authModal = useAuthModalStore()
const session = useSessionStore()
</script>

<template>
  <header class="header">
    <div class="container header__container">
      <RouterLink to="/" class="header__logo-link" aria-label="StudyAI — главная страница">
        <img :src="logo" alt="StudyAI" class="header__logo" />
      </RouterLink>

      <div class="header__actions">
        <RouterLink
          v-if="session.isAuthenticated"
          to="/account"
          class="text-link text-3 header__account"
          aria-label="Личный кабинет"
          title="Личный кабинет"
        >
          <CircleUserRound :size="28" aria-hidden="true" />
          <span>Личный кабинет</span>
        </RouterLink>
        <template v-if="session.isAuthenticated">
          <BaseButton
            variant="transparent"
            size="small"
            :loading="session.isPending"
            @click="session.logout"
            >Выйти</BaseButton
          >
        </template>
        <template v-else>
          <BaseButton
            variant="transparent"
            size="small"
            aria-haspopup="dialog"
            :disabled="session.isInitializing || session.isPending"
            @click="authModal.open('login')"
          >
            Войти
          </BaseButton>

          <BaseButton
            variant="yellow"
            size="small"
            aria-haspopup="dialog"
            :disabled="session.isInitializing || session.isPending"
            @click="authModal.open('register')"
          >
            Зарегистрироваться
          </BaseButton>
        </template>
      </div>
    </div>
    <div v-if="session.sessionError" class="container header__status text-4" role="alert">
      <p>{{ session.sessionError }}</p>
      <button
        type="button"
        :disabled="session.isInitializing || session.isPending"
        @click="session.initialize"
      >
        Повторить
      </button>
    </div>
  </header>
</template>

<style scoped>
.header {
  position: fixed;
  inset: 0 0 auto;
  z-index: 50;

  width: 100%;

  background: linear-gradient(
    to bottom,
    var(--color-header-background) 0%,
    color-mix(in srgb, var(--color-background) 50%, transparent) 55%,
    transparent 100%
  );
}

.header__container {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 32px;
  min-height: var(--header-height);
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
.header__account {
  white-space: nowrap;
}
.header__account svg {
  flex-shrink: 0;
}
.header__status {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 16px;
  padding-block: 8px;
  color: var(--color-yellow);
}
.header__status button {
  border: 0;
  background: transparent;
  color: inherit;
  text-decoration: underline;
}

@media (max-width: 768px) {
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
  .header__account {
    gap: 0;
  }
  .header__account span {
    display: none;
  }
}
</style>
