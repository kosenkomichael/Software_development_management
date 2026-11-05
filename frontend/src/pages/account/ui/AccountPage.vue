<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowRight, BarChart2, BookOpen, CheckSquare, LogOut, Pencil } from 'lucide-vue-next'
import { ProfileEditor } from '@/features/edit-profile'
import { useMaterialLibraryStore } from '@/features/material-library'
import { useSessionStore } from '@/entities/session'
import { formatSize } from '@/entities/material'
import { BaseButton } from '@/shared/ui/button'
import { designAssets } from '@/shared/assets'
const session = useSessionStore()
const library = useMaterialLibraryStore()
const router = useRouter()
const editing = ref(false)
const username = computed(() => session.user?.first_name?.trim() || session.user?.email.split('@')[0] || 'Гость')
const initial = computed(() => Array.from(username.value.trim())[0]?.toLocaleUpperCase('ru-RU') || 'Г')
const recent = computed(() => library.items.slice(0, 3))
onMounted(() => {
  void library.load()
})
async function logout() {
  await session.logout()
  void router.replace('/')
}
</script>

<template>
  <div class="workspace-page account-page">
    <header class="section-heading">
      <div class="page-heading">
        <h1 class="title-1">Личный кабинет</h1>
        <p class="text-1 muted">Добро пожаловать, {{ username }}!</p>
      </div>
      <BaseButton class="account-page__logout" :loading="session.isPending" @click="logout"
        ><template #icon-left><LogOut /></template>Выйти</BaseButton
      >
    </header>
    <section
      class="surface account-page__profile"
      :style="{ backgroundImage: `url(${designAssets.uploadBackground})` }"
    >
      <span class="account-page__avatar title-1" aria-hidden="true">{{ initial }}</span>
      <div class="account-page__identity">
        <h2 class="title-4">{{ username }}</h2>
        <p class="text-2 muted">{{ session.user?.email }}</p>
        <span class="badge text-4">студент</span>
      </div>
      <BaseButton class="account-page__edit" variant="transparent" @click="editing = true"
        ><template #icon-left><Pencil /></template>Редактировать профиль</BaseButton
      >
    </section>
    <div v-if="library.error" class="notice text-3" role="alert">
      {{ library.error }} <button class="text-link" @click="library.load(true)">Повторить</button>
    </div>
    <div class="account-page__stats">
      <article class="surface account-page__stat">
        <span class="account-page__stat-icon account-page__stat-icon--materials"
          ><BookOpen :size="55"
        /></span>
        <div>
          <strong class="title-3">{{ library.loaded ? library.total : '—' }}</strong>
          <p class="text-1">Материалов</p>
          <p class="text-3 muted">в вашей библиотеке</p>
        </div>
      </article>
      <article class="surface account-page__stat">
        <span class="account-page__stat-icon account-page__stat-icon--tests"
          ><CheckSquare :size="55"
        /></span>
        <div>
          <strong class="title-3">—</strong>
          <p class="text-1">Пройдено тестов</p>
          <p class="text-3 muted">История пока недоступна</p>
        </div>
      </article>
      <article class="surface account-page__stat">
        <span class="account-page__stat-icon account-page__stat-icon--score"
          ><BarChart2 :size="55"
        /></span>
        <div>
          <strong class="title-3">—</strong>
          <p class="text-1">Средний результат</p>
          <p class="text-3 muted">Статистика появится позже</p>
        </div>
      </article>
    </div>
    <section class="surface account-page__continue">
      <header class="section-heading">
        <h2 class="title-4">Продолжить обучение</h2>
        <RouterLink class="text-link text-4" to="/materials"
          >Все материалы <ArrowRight :size="20"
        /></RouterLink>
      </header>
      <p v-if="library.loading" class="text-3 muted" role="status">Загружаем библиотеку…</p>
      <p v-else-if="!recent.length" class="text-3 muted">
        Загрузите первую лекцию и начните обучение.
      </p>
      <div v-else class="account-page__recent">
        <RouterLink
          v-for="item in recent"
          :key="item.id"
          :to="`/materials/${item.id}`"
          class="account-page__recent-item text-2"
          ><BookOpen :size="26" /><span>{{ item.original_filename }}</span
          ><ArrowRight :size="22"
        /></RouterLink>
      </div>
      <BaseButton v-if="!recent.length && !library.loading" @click="router.push('/materials/new')"
        >Добавить материал</BaseButton
      >
    </section>
    <div class="account-page__bottom">
      <section class="surface account-page__storage">
        <header class="section-heading">
          <h2 class="title-4">Хранилище</h2>
          <button
            class="text-link text-4"
            type="button"
            disabled
            title="Увеличение лимита пока недоступно"
          >
            Увеличить лимит <ArrowRight :size="20" />
          </button>
        </header>
        <p class="text-3 muted">
          {{ library.loaded ? `Использовано ${formatSize(library.bytes)}` : 'Загружаем данные…' }}
        </p>
        <div class="account-page__track" aria-hidden="true" />
        <p class="text-4 muted">Информация о лимите появится позже.</p>
      </section>
      <section class="surface account-page__activity">
        <header class="section-heading">
          <h2 class="title-4">Недавняя активность</h2>
          <button
            class="text-link text-4"
            type="button"
            disabled
            title="История активности пока недоступна"
          >
            Смотреть все <ArrowRight :size="20" />
          </button>
        </header>
        <p class="text-3 muted">История обучения пока недоступна.</p>
      </section>
    </div>
    <ProfileEditor :open="editing" @close="editing = false" />
  </div>
</template>
<style scoped>
.account-page {
  gap: 26px;
}
.account-page header .page-heading {
  margin-bottom: 0;
}
.account-page__logout {
  min-width: 170px;
  min-height: 52px;
  border-radius: var(--border-radius-md);
  font-size: var(--font-size-text-2);
}
.account-page__profile {
  display: flex;
  align-items: center;
  gap: 36px;
  min-height: 180px;
  padding: 28px 40px;
  background-size: cover;
  background-position: center;
}
.account-page__avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 120px;
  height: 120px;
  flex-shrink: 0;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--color-yellow), var(--color-orange));
  color: var(--color-background);
  font-weight: var(--font-weight-semibold);
}
.account-page__identity {
  flex: 1;
  min-width: 0;
}
.account-page__identity .badge {
  margin-top: 12px;
}
.account-page__edit {
  align-self: flex-start;
  border-radius: var(--border-radius-md);
  font-size: var(--font-size-text-2);
}
.account-page__stats {
  display: flex;
  gap: 28px;
}
.account-page__stat {
  display: flex;
  align-items: center;
  gap: 24px;
  flex: 1;
  min-width: 0;
  padding: 26px 22px;
  min-height: 159px;
}
.account-page__stat-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 95px;
  height: 95px;
  border-radius: var(--border-radius-md);
  flex-shrink: 0;
}
.account-page__stat-icon--materials {
  color: var(--color-yellow);
  background: var(--color-active);
}
.account-page__stat-icon--tests {
  color: var(--color-success);
  background: color-mix(in srgb, var(--color-success) 30%, transparent);
}
.account-page__stat-icon--score {
  color: var(--color-info);
  background: color-mix(in srgb, var(--color-info) 25%, transparent);
}
.account-page__continue {
  display: flex;
  flex-direction: column;
  gap: 24px;
  padding: 24px;
  min-height: 227px;
}
.account-page__continue > .base-button {
  align-self: flex-start;
}
.account-page__recent {
  display: flex;
  gap: 20px;
}
.account-page__recent-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  min-width: 0;
  flex: 1;
  color: var(--color-text-primary);
  text-decoration: none;
  border-radius: var(--radius-card);
  background: var(--color-background);
}
.account-page__recent-item span {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.account-page__recent-item svg {
  flex-shrink: 0;
  color: var(--color-yellow);
}
.account-page__bottom {
  display: flex;
  gap: 24px;
}
.account-page__bottom > * {
  display: flex;
  flex-direction: column;
  gap: 18px;
  padding: 24px;
  flex: 1;
  min-width: 0;
  min-height: 183px;
}
.account-page__track {
  height: 14px;
  max-width: 560px;
  border-radius: var(--border-radius-lg);
  background: var(--color-track);
}
@media (max-width: 768px) {
  .account-page__profile {
    flex-wrap: wrap;
    gap: 16px;
    min-height: 0;
    padding: 20px;
  }
  .account-page__avatar {
    width: 84px;
    height: 84px;
  }
  .account-page__edit {
    align-self: stretch;
    text-align: center;
  }
  .account-page__stats,
  .account-page__recent,
  .account-page__bottom {
    flex-direction: column;
  }
  .account-page__stat-icon {
    width: 64px;
    height: 64px;
  }
  .account-page__logout {
    min-width: 0;
    flex: 1;
  }
}
</style>
