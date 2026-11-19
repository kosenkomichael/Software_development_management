<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { LogOut } from 'lucide-vue-next'

import { Profile, Stats, Overview } from '@/widgets/account-profile'

import { useSessionStore } from '@/entities/session'
import { BaseButton } from '@/shared/ui/button'

const session = useSessionStore()
const router = useRouter()

const username = computed(
  () => session.user?.first_name?.trim() || session.user?.email.split('@')[0] || 'Гость'
)

async function logout() {
  await session.logout()
  void router.replace('/')
}
</script>

<template>
  <div class="workspace-page account-page">
    <header class="section-heading account-page__header">
      <div class="page-heading">
        <h1 class="title-2">Личный кабинет</h1>
        <p class="text-1 muted">Добро пожаловать, {{ username }}!</p>
      </div>

      <BaseButton
        class="account-page__logout"
        size="small"
        :loading="session.isPending"
        @click="logout"
      >
        <template #icon-left>
          <LogOut :size="20" />
        </template>
        Выйти
      </BaseButton>

      <button
        class="account-page__logout-mobile"
        type="button"
        aria-label="Выйти из аккаунта"
        title="Выйти"
        :disabled="session.isPending"
        @click="logout"
      >
        <LogOut :size="24" :stroke-width="2.5" aria-hidden="true" />
      </button>
    </header>

    <Profile />

    <Stats />

    <Overview />
  </div>
</template>

<style scoped>
.account-page {
  gap: 16px;
}

.account-page header .page-heading {
  margin-bottom: 0;
}

.account-page__logout {
  min-width: 130px;
  min-height: 44px;
  border-radius: var(--radius-card);
}

.account-page__logout-mobile {
  display: none;
}

@media (max-width: 768px) {
  .account-page__header {
    display: flex;
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
    flex-wrap: nowrap;
    gap: 12px;
  }

  .account-page__header .page-heading {
    flex: 1;
    min-width: 0;
    margin-bottom: 0;
  }

  .account-page__logout {
    display: none;
  }

  .account-page__logout-mobile {
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;

    width: 48px;
    height: 48px;
    padding: 0;

    border: none;
    border-radius: 14px;

    background-color: var(--color-yellow);
    color: var(--color-dark);

    cursor: pointer;
  }

  .account-page__logout-mobile svg {
    display: block;
    flex-shrink: 0;
  }

  .account-page__logout-mobile:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
}
</style>
