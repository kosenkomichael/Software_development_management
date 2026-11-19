<script setup lang="ts">
import { computed, ref } from 'vue'
import { Pencil } from 'lucide-vue-next'

import { ProfileEditor } from '@/features/edit-profile'
import { useSessionStore } from '@/entities/session'
import { BaseButton } from '@/shared/ui/button'
import { designAssets } from '@/shared/assets'

const session = useSessionStore()
const editing = ref(false)

const username = computed(
  () => session.user?.first_name?.trim() || session.user?.email.split('@')[0] || 'Гость'
)

const initial = computed(
  () => Array.from(username.value.trim())[0]?.toLocaleUpperCase('ru-RU') || 'Г'
)
</script>

<template>
  <section
    class="surface account-profile"
    :style="{ backgroundImage: `url(${designAssets.uploadBackground})` }"
  >
    <span class="account-profile__avatar title-3" aria-hidden="true">
      {{ initial }}
    </span>

    <div class="account-profile__identity">
      <h2 class="title-4">{{ username }}</h2>
      <p class="text-3 muted">{{ session.user?.email }}</p>
      <span class="badge text-4">студент</span>
    </div>

    <BaseButton
      class="account-profile__edit"
      variant="transparent"
      size="small"
      @click="editing = true"
    >
      <template #icon-left>
        <Pencil :size="18" />
      </template>
      Редактировать профиль
    </BaseButton>
  </section>

  <ProfileEditor :open="editing" @close="editing = false" />
</template>

<style scoped>
.account-profile {
  display: flex;
  align-items: center;
  gap: 20px;

  min-height: 110px;
  padding: 16px 24px;

  background-size: cover;
  background-position: center;
}

.account-profile__avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;

  width: 72px;
  height: 72px;

  border-radius: 50%;
  background: linear-gradient(135deg, var(--color-yellow), var(--color-orange));
  color: var(--color-background);
  font-weight: var(--font-weight-semibold);
}

.account-profile__identity {
  flex: 1;
  min-width: 0;
}

.account-profile__identity p {
  margin-top: 4px;
  overflow-wrap: anywhere;
}

.account-profile__identity .badge {
  margin-top: 8px;
}

.account-profile__edit {
  flex-shrink: 0;
  align-self: center;
  min-height: 44px;
  border-radius: var(--radius-card);
}

@media (max-width: 768px) {
  .account-profile {
    flex-wrap: wrap;
    gap: 16px;
    padding: 20px;
  }

  .account-profile__avatar {
    width: 60px;
    height: 60px;
  }

  .account-profile__edit {
    width: 100%;
  }
}
</style>
