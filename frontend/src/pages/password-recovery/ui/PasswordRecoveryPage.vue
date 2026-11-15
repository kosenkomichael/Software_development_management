<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from 'vue'
import { useRouter } from 'vue-router'
import { apiRequest } from '@/shared/api'
import { BaseButton } from '@/shared/ui/button'
import { useAuthModalStore } from '@/features/auth'

const props = defineProps<{ reset?: boolean }>()
const router = useRouter()
const auth = useAuthModalStore()
const token = new URLSearchParams(window.location.hash.slice(1)).get('token') ?? ''
// Remove the secret from the address bar and browser history.
if (props.reset) window.history.replaceState(window.history.state, '', window.location.pathname)
const email = ref('')
const password = ref('')
const confirmation = ref('')
const pending = ref(false)
const done = ref(false)
const error = ref('')
const resendAt = ref(0)
const now = ref(Date.now())
const timer = setInterval(() => { now.value = Date.now() }, 1000)
const remaining = computed(() => Math.max(0, Math.ceil((resendAt.value - now.value) / 1000)))
function editEmail() {
  done.value = false
  error.value = ''
}

let disposed = false
onBeforeUnmount(() => { disposed = true; clearInterval(timer) })
const invalidLink = computed(() => props.reset && !token)

async function submit() {
  if (pending.value) return
  error.value = ''
  if (props.reset && password.value !== confirmation.value) {
    error.value = 'Пароли не совпадают.'
    return
  }
  pending.value = true
  try {
    if (props.reset) {
      await apiRequest('/auth/reset-password', {
        method: 'POST', body: JSON.stringify({ token, password: password.value }),
      })
    } else {
      const response = await apiRequest<{ retry_after: number }>('/auth/forgot-password', {
        method: 'POST', body: JSON.stringify({ email: email.value.trim() }),
      })
      if (!disposed) {
        now.value = Date.now()
        resendAt.value = now.value + response.retry_after * 1000
      }
    }
    if (!disposed) done.value = true
    password.value = ''
    confirmation.value = ''
  } catch (reason) {
    if (!disposed) error.value = reason instanceof Error ? reason.message : 'Не удалось выполнить запрос.'
  } finally {
    if (!disposed) pending.value = false
  }
}
function login() {
  void router.push('/')
  auth.open('login')
}
</script>

<template>
  <main class="recovery surface">
    <h1 class="title-3">{{ reset ? 'Новый пароль' : 'Восстановление пароля' }}</h1>
    <template v-if="done">
      <p class="text-2" role="status">
        <template v-if="reset">Пароль изменён. Войдите с новым паролем.</template>
        <template v-else>Проверьте почту {{ email.trim() }}. Мы отправляем ссылку для смены пароля. Она действует 30 минут.</template>
      </p>
      <template v-if="!reset">
        <p class="text-2 muted">Не видите письмо? Проверьте папку «Спам» или отправьте его ещё раз.</p>
        <p v-if="error" class="text-2 danger" role="alert">{{ error }}</p>
        <BaseButton :loading="pending" :disabled="remaining > 0" @click="submit">
          {{ remaining > 0 ? `Отправить повторно через ${remaining} с` : 'Отправить повторно' }}
        </BaseButton>
        <button type="button" class="text-2 recovery__back" :disabled="pending" @click="editEmail">Изменить email</button>
      </template>
      <BaseButton @click="login">Вернуться ко входу</BaseButton>
    </template>
    <template v-else-if="invalidLink">
      <p class="text-2 danger" role="alert">В ссылке нет кода восстановления. Запросите новое письмо.</p>
      <RouterLink to="/forgot-password">Получить новую ссылку</RouterLink>
    </template>
    <form v-else :aria-busy="pending" @submit.prevent="submit">
      <p class="text-2">{{ reset ? 'Придумайте пароль от 8 до 128 символов.' : 'Укажите email вашего аккаунта. Мы отправим ссылку для смены пароля.' }}</p>
      <template v-if="reset">
        <label class="app-field text-2">Новый пароль
          <input v-model="password" class="app-input" type="password" autocomplete="new-password" minlength="8" maxlength="128" required :disabled="pending" />
        </label>
        <label class="app-field text-2">Повторите пароль
          <input v-model="confirmation" class="app-input" type="password" autocomplete="new-password" minlength="8" maxlength="128" required :disabled="pending" />
        </label>
      </template>
      <label v-else class="app-field text-2">Email
        <input v-model="email" class="app-input" type="email" autocomplete="email" maxlength="254" required :disabled="pending" />
      </label>
      <p v-if="error" class="text-2 danger" role="alert">{{ error }}</p>
      <BaseButton type="submit" :loading="pending">{{ reset ? 'Сохранить пароль' : 'Отправить письмо' }}</BaseButton>
      <RouterLink v-if="reset" to="/forgot-password">Запросить новую ссылку</RouterLink>
      <button type="button" class="text-2 recovery__back" :disabled="pending" @click="login">Вернуться ко входу</button>
    </form>
  </main>
</template>

<style scoped>
.recovery { width: min(520px, calc(100% - 32px)); margin: 64px auto; padding: 32px; display: flex; flex-direction: column; gap: 24px; }
.recovery form { display: flex; flex-direction: column; gap: 20px; }
.recovery__back { background: transparent; border: 0; color: var(--color-text-primary); cursor: pointer; }
@media (max-width: 768px) { .recovery { margin: 24px auto; padding: 20px; } }
</style>
