<script setup lang="ts">
import { computed, ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { ArrowLeft, BookOpen, ChevronRight, File, FilePlus, Heart, Users } from 'lucide-vue-next'
import { useSessionStore } from '@/entities/session'
import logo from '@/shared/assets/images/logo.svg'

const session = useSessionStore()
const route = useRoute()
const compact = ref(false)
const displayName = computed(
  () => session.user?.first_name?.trim() || session.user?.email.split('@')[0] || 'Гость'
)
const initial = computed(
  () => Array.from(displayName.value.trim())[0]?.toLocaleUpperCase('ru-RU') || 'Г'
)
const links = [
  { to: '/materials', label: 'Мои материалы', icon: File },
  { to: '/materials/new', label: 'Добавить материал', icon: FilePlus },
  { to: '/community', label: 'Сообщество', icon: Users },
  { to: '/favorites', label: 'Избранное', icon: Heart },
]
function isActive(path: string) {
  if (path === '/materials') return route.name === 'materials' || route.name === 'material'
  if (path === '/materials/new')
    return route.name === 'create-material' || route.name === 'material-processing'
  return route.path === path
}
</script>

<template>
  <aside class="surface sidebar" :class="{ 'sidebar--compact': compact }">
    <div class="sidebar__brand">
      <RouterLink to="/" class="sidebar__logo" aria-label="StudyAI — главная" title="На главную">
        <BookOpen v-if="compact" :size="30" aria-hidden="true" />
        <img v-else :src="logo" alt="StudyAI" />
      </RouterLink>
      <button
        class="icon-button sidebar__toggle"
        type="button"
        :aria-label="compact ? 'Развернуть меню' : 'Свернуть меню'"
        :title="compact ? 'Развернуть меню' : 'Свернуть меню'"
        :aria-expanded="!compact"
        aria-controls="sidebar-navigation"
        @click="compact = !compact"
      >
        <ArrowLeft :size="20" aria-hidden="true" />
      </button>
    </div>
    <nav id="sidebar-navigation" class="sidebar__nav" aria-label="Основное меню">
      <RouterLink
        v-for="link in links"
        :key="link.to"
        :to="link.to"
        :title="link.label"
        :aria-label="link.label"
        :aria-current="isActive(link.to) ? 'page' : undefined"
        class="sidebar__link text-2"
        :class="{ 'sidebar__link--active': isActive(link.to) }"
      >
        <component :is="link.icon" :size="24" aria-hidden="true" />
        <span v-if="!compact" class="sidebar__label">{{ link.label }}</span>
      </RouterLink>
    </nav>
    <div class="sidebar__bottom">
      <RouterLink
        to="/account"
        class="sidebar__link sidebar__user"
        :class="{ 'sidebar__link--active': route.path === '/account' }"
        :aria-label="`Личный кабинет: ${displayName}`"
        :aria-current="route.path === '/account' ? 'page' : undefined"
        :title="compact ? displayName : undefined"
      >
        <span class="sidebar__avatar text-2" aria-hidden="true">{{ initial }}</span>
        <div v-if="!compact" class="sidebar__identity">
          <span class="text-2">{{ displayName }}</span>
          <span class="text-4 muted">{{
            session.isAuthenticated ? 'Студент' : 'Демонстрация'
          }}</span>
        </div>
        <ChevronRight v-if="!compact" class="sidebar__chevron" :size="20" aria-hidden="true" />
      </RouterLink>
    </div>
  </aside>
</template>

<style scoped>
.sidebar {
  position: sticky;
  top: 50px;
  display: flex;
  flex-direction: column;
  flex: 0 0 clamp(260px, 20vw, 385px);
  width: clamp(260px, 20vw, 385px);
  min-height: calc(100svh - 100px);
  padding: 28px 20px 20px;
  border-radius: var(--radius-panel);
  transition:
    width var(--transition-default),
    flex-basis var(--transition-default),
    padding var(--transition-default);
}
.sidebar__brand {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  min-height: 48px;
  margin-bottom: 40px;
}
.sidebar__logo {
  display: flex;
  align-items: center;
  min-width: 0;
  color: var(--color-yellow);
  text-decoration: none;
}
.sidebar__logo img {
  width: 168px;
  height: auto;
}
.sidebar__toggle {
  width: 36px;
  height: 36px;
}
.sidebar__toggle svg {
  transition: transform var(--transition-default);
}
.sidebar__nav {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 40px;
}
.sidebar__link {
  position: relative;
  isolation: isolate;
  display: flex;
  align-items: center;
  gap: 16px;
  min-height: 58px;
  padding: 12px 14px;
  border: 1px solid transparent;
  border-radius: var(--radius-card);
  color: var(--color-text-secondary);
  text-decoration: none;
  white-space: nowrap;
  transition:
    color var(--transition-default),
    border-color var(--transition-default),
    box-shadow var(--transition-default);
}
.sidebar__link::before {
  content: '';
  position: absolute;
  inset: 0;
  z-index: -1;
  border-radius: inherit;
  background: linear-gradient(
    90deg,
    color-mix(in srgb, var(--color-orange) 42%, transparent) 0%,
    color-mix(in srgb, var(--color-orange) 20%, transparent) 48%,
    color-mix(in srgb, var(--color-orange) 4%, transparent) 100%
  );
  opacity: 0;
  pointer-events: none;
  transition: opacity var(--transition-default);
}
.sidebar__link svg {
  flex-shrink: 0;
}
.sidebar__label {
  overflow: hidden;
  text-overflow: ellipsis;
}
.sidebar__link:hover,
.sidebar__link:focus-visible {
  color: var(--color-yellow);
  border-color: color-mix(in srgb, var(--color-orange) 22%, transparent);
}
.sidebar__link:hover::before,
.sidebar__link:focus-visible::before {
  opacity: 0.65;
}
.sidebar__link--active {
  color: var(--color-yellow);
  border-color: color-mix(in srgb, var(--color-orange) 25%, transparent);
  box-shadow:
    inset 2px 0 0 var(--color-yellow),
    0 4px 18px color-mix(in srgb, var(--color-orange) 8%, transparent);
}
.sidebar__link--active::before,
.sidebar__link--active:hover::before {
  opacity: 1;
}
.sidebar__bottom {
  margin-top: auto;
  padding-top: 24px;
  border-top: 1px solid var(--color-border-muted);
}
.sidebar__user {
  min-height: 76px;
  gap: 14px;
  padding: 12px;
  color: var(--color-text-primary);
}
.sidebar__avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  flex-shrink: 0;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--color-yellow), var(--color-orange));
  color: var(--color-background);
  font-weight: var(--font-weight-semibold);
}
.sidebar__identity {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
  flex: 1;
}
.sidebar__identity span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.sidebar__chevron {
  color: var(--color-text-secondary);
}
.sidebar--compact {
  width: 92px;
  flex-basis: 92px;
  padding: 24px 16px 20px;
}
.sidebar--compact .sidebar__brand {
  flex-direction: column;
  gap: 16px;
  margin-bottom: 24px;
}
.sidebar--compact .sidebar__logo {
  justify-content: center;
  width: 56px;
  height: 44px;
}
.sidebar--compact .sidebar__toggle {
  width: 56px;
  height: 36px;
}
.sidebar--compact .sidebar__toggle svg {
  transform: rotate(180deg);
}
.sidebar--compact .sidebar__link {
  justify-content: center;
  width: 56px;
  min-height: 56px;
  padding: 0;
  gap: 0;
}
.sidebar--compact .sidebar__bottom {
  padding-top: 20px;
}
.sidebar--compact .sidebar__user {
  min-height: 64px;
}
@media (max-width: 768px) {
  .sidebar {
    position: sticky;
    top: 12px;
    flex: 0 0 72px;
    width: 72px;
    padding: 16px 8px;
    min-height: calc(100svh - 24px);
  }
  .sidebar__toggle {
    display: none;
  }
  .sidebar__label,
  .sidebar__identity,
  .sidebar__chevron {
    display: none;
  }
  .sidebar__logo img {
    width: 40px;
  }
  .sidebar__link {
    justify-content: center;
    gap: 0;
    padding: 12px 0;
    min-height: 52px;
  }
  .sidebar__user {
    justify-content: center;
    min-height: 56px;
    padding: 6px;
  }
}
</style>
