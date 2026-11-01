<script setup lang="ts">
import { nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { BaseModal } from '@/shared/ui/modal'
import { useSessionStore } from '@/entities/session'
import { useAuthModalStore } from '../model'
import AuthIllustration from './AuthIllustration.vue'
import LoginForm from './LoginForm.vue'

const authModal = useAuthModalStore()
const session = useSessionStore()
const router = useRouter()
function onAuthenticated() {
  const target = authModal.redirectTo
  authModal.redirectTo = ''
  authModal.close()
  void router.push(target.startsWith('/') && !target.startsWith('//') ? target : '/account')
}

async function onRegistered(email: string) {
  authModal.registered(email)
  await nextTick()
  document.querySelector<HTMLInputElement>('#login-panel input[name="email"]')?.focus()
}

function onTabKeydown(event: KeyboardEvent) {
  if (session.isPending) return
  if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return
  event.preventDefault()
  const mode =
    event.key === 'Home'
      ? 'login'
      : event.key === 'End'
        ? 'register'
        : authModal.mode === 'login'
          ? 'register'
          : 'login'
  authModal.mode = mode
  const target = event.currentTarget as HTMLElement
  target.querySelector<HTMLButtonElement>(`#${mode}-tab`)?.focus()
}
</script>

<template>
  <BaseModal
    :style="{
      '--modal-radius': '30px',
      '--modal-background': 'var(--color-auth-surface)',
      '--modal-border-color': 'var(--color-auth-input)',
    }"
    :open="authModal.isOpen"
    labelledby="auth-title"
    @close="authModal.close"
  >
    <div v-if="authModal.isOpen" class="auth-modal">
      <AuthIllustration />
      <div class="auth-modal__panel">
        <div
          class="auth-modal__tabs"
          role="tablist"
          aria-label="Авторизация"
          @keydown="onTabKeydown"
        >
          <button
            id="login-tab"
            class="text-1 auth-modal__tab"
            :class="{ 'auth-modal__tab--active': authModal.mode === 'login' }"
            role="tab"
            :disabled="session.isPending"
            :aria-selected="authModal.mode === 'login'"
            :tabindex="authModal.mode === 'login' ? 0 : -1"
            @click="authModal.mode = 'login'"
            aria-controls="login-panel"
            type="button"
          >
            Вход
          </button>
          <button
            id="register-tab"
            class="text-1 auth-modal__tab"
            :class="{ 'auth-modal__tab--active': authModal.mode === 'register' }"
            role="tab"
            :disabled="session.isPending"
            :aria-selected="authModal.mode === 'register'"
            :tabindex="authModal.mode === 'register' ? 0 : -1"
            aria-controls="register-panel"
            @click="authModal.mode = 'register'"
            type="button"
          >
            Регистрация
          </button>
        </div>
        <div
          :id="`${authModal.mode}-panel`"
          class="auth-modal__content"
          role="tabpanel"
          :aria-labelledby="`${authModal.mode}-tab`"
        >
          <h2 id="auth-title" class="title-3 auth-modal__title">
            Добро пожаловать<br />в <span>StudyAI</span>
          </h2>
          <p v-if="authModal.mode === 'login'" class="auth-modal__description text-2">
            Войдите в свой аккаунт, чтобы продолжить работу с материалами
          </p>
          <LoginForm
            :key="authModal.mode"
            :mode="authModal.mode"
            :initial-email="authModal.email"
            :notice="authModal.notice"
            @registered="onRegistered"
            @authenticated="onAuthenticated"
          />
        </div>
      </div>
    </div>
  </BaseModal>
</template>

<style scoped>
.auth-modal {
  display: flex;
  width: 1000px;
  min-height: 900px;
  zoom: 0.85;
}
.auth-modal__panel {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-width: 0;
  padding: 67px 40px 25px 28px;
  background: transparent;
}
.auth-modal__tabs {
  display: flex;
  min-height: 58px;
  flex-shrink: 0;
  border-bottom: 3px solid var(--color-border-muted);
}
.auth-modal__tab {
  flex: 1;
  padding: 0 0 28px;
  border: 0;
  background: transparent;
  color: var(--color-text-primary);
  line-height: 1.2;
  font-weight: var(--font-weight-semibold);
}
.auth-modal__tab:first-child {
  flex: 0 0 200px;
}
.auth-modal__tab--active {
  color: var(--color-yellow);
  box-shadow: 0 3px 0 var(--color-yellow);
}
.auth-modal__content {
  display: flex;
  flex-direction: column;
  flex: 1;
  padding-top: 42px;
}
.auth-modal__title {
  line-height: 1.2;
}
.auth-modal__title span {
  color: var(--color-yellow);
}
.auth-modal__description {
  margin-top: 23px;
  min-height: 105px;
  line-height: 35px;
  color: var(--color-text-secondary);
}
</style>
