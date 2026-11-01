<script setup lang="ts">
import { watch } from 'vue'
import { RouterView, useRouter } from 'vue-router'
import { AppSidebar } from '@/widgets/sidebar'
import { useSessionStore } from '@/entities/session'
import { useAuthModalStore } from '@/features/auth'
const session = useSessionStore()
const router = useRouter()
watch(
  () => session.isAuthenticated,
  (authenticated) => {
    if (!authenticated && !session.isInitializing) void router.replace('/')
  }
)
function login() {
  useAuthModalStore().open('login')
}
</script>

<template>
  <div
    v-if="session.isAuthenticated || $route.meta.publicPreview"
    class="workspace-layout"
    :class="{ 'workspace-layout--detail': $route.meta.materialDetail }"
  >
    <AppSidebar />
    <main id="workspace-content" class="workspace-layout__content"><RouterView /></main>
  </div>
  <main v-else class="empty-state">
    <h1 class="title-3">Войдите в StudyAI</h1>
    <button class="text-link text-2" type="button" @click="login">Открыть окно входа</button>
  </main>
</template>

<style scoped>
.workspace-layout {
  display: flex;
  align-items: flex-start;
  gap: 30px;
  padding: 30px;
  min-height: 100svh;
}
.workspace-layout__content {
  flex: 1;
  min-width: 0;
  padding-top: 22px;
}
.workspace-layout--detail {
  background: radial-gradient(
    ellipse at 20% 0%,
    color-mix(in srgb, var(--color-orange) 8%, transparent),
    transparent 45%
  );
}
</style>
