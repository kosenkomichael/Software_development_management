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
    <header class="section-heading">
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

@media (max-width: 768px) {
  .account-page__logout {
    min-width: 0;
  }
}
</style>
