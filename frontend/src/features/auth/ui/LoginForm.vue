<script setup lang="ts">
import { onBeforeUnmount, reactive, ref } from 'vue'
import { Lock, User } from 'lucide-vue-next'
import { BaseButton } from '@/shared/ui/button'
import { useSessionStore } from '@/entities/session'

const props = withDefaults(
  defineProps<{
    mode?: 'login' | 'register'
    initialEmail?: string
    notice?: string
  }>(),
  { mode: 'login', initialEmail: '', notice: '' }
)
const emit = defineEmits<{ registered: [email: string]; authenticated: [] }>()
const session = useSessionStore()
let disposed = false
onBeforeUnmount(() => {
  disposed = true
})

const login = ref(props.initialEmail)
const password = ref('')
const passwordConfirmation = ref('')
const remember = ref(false)
const loginInput = ref<HTMLInputElement>()
const passwordInput = ref<HTMLInputElement>()
const confirmationInput = ref<HTMLInputElement>()
const errors = reactive({ login: '', password: '', confirmation: '' })
const status = ref(props.notice)
const isError = ref(false)

function clearError(field: keyof typeof errors) {
  errors[field] = ''
  if (field === 'password') errors.confirmation = ''
  status.value = ''
  isError.value = false
}

async function submit() {
  if (session.isPending || session.isInitializing) return
  status.value = ''
  isError.value = false
  const email = login.value.trim().toLowerCase()
  errors.login = !email
    ? 'Введите email'
    : !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email) || email.length > 254
      ? 'Введите корректный email'
      : ''
  errors.password = password.value ? '' : 'Введите пароль'
  if (
    props.mode === 'register' &&
    password.value &&
    (password.value.length < 8 || password.value.length > 128)
  ) {
    errors.password = 'Пароль должен содержать от 8 до 128 символов'
  }
  errors.confirmation =
    props.mode === 'register'
      ? !passwordConfirmation.value
        ? 'Повторите пароль'
        : passwordConfirmation.value !== password.value
          ? 'Пароли не совпадают'
          : ''
      : ''
  if (errors.login) loginInput.value?.focus()
  else if (errors.password) passwordInput.value?.focus()
  else if (errors.confirmation) confirmationInput.value?.focus()
  else {
    try {
      if (props.mode === 'register') {
        await session.register({ email, password: password.value })
        if (!disposed) emit('registered', email)
      } else {
        await session.login({ email, password: password.value }, remember.value)
        if (!disposed) emit('authenticated')
      }
      password.value = ''
      passwordConfirmation.value = ''
    } catch (error) {
      if (disposed) return
      isError.value = true
      status.value =
        error instanceof Error ? error.message : 'Не удалось выполнить запрос. Попробуйте ещё раз.'
    }
  }
}
</script>

<template>
  <form
    class="login-form"
    :class="{ 'login-form--register': mode === 'register' }"
    :aria-busy="session.isPending"
    novalidate
    @submit.prevent="submit"
  >
    <div class="login-form__fields">
      <div class="login-form__field">
        <label class="login-form__input-wrap">
          <User :size="30" aria-hidden="true" />
          <input
            ref="loginInput"
            class="text-1"
            v-model="login"
            data-modal-autofocus
            name="email"
            type="email"
            inputmode="email"
            :disabled="session.isPending"
            autocomplete="username"
            aria-label="Email"
            placeholder="Email"
            required
            :aria-invalid="!!errors.login"
            :aria-describedby="errors.login ? 'login-error' : undefined"
            @input="clearError('login')"
          />
        </label>
        <p v-if="errors.login" id="login-error" class="text-4 login-form__error" role="alert">
          {{ errors.login }}
        </p>
      </div>
      <div class="login-form__field">
        <label class="login-form__input-wrap">
          <Lock :size="30" aria-hidden="true" />
          <input
            ref="passwordInput"
            class="text-1"
            v-model="password"
            name="password"
            :disabled="session.isPending"
            type="password"
            :autocomplete="mode === 'register' ? 'new-password' : 'current-password'"
            aria-label="Пароль"
            placeholder="Пароль"
            required
            :aria-invalid="!!errors.password"
            :aria-describedby="errors.password ? 'password-error' : undefined"
            @input="clearError('password')"
          />
        </label>
        <p v-if="errors.password" id="password-error" class="text-4 login-form__error" role="alert">
          {{ errors.password }}
        </p>
      </div>
      <div v-if="mode === 'register'" class="login-form__field">
        <label class="login-form__input-wrap">
          <Lock :size="30" aria-hidden="true" />
          <input
            ref="confirmationInput"
            v-model="passwordConfirmation"
            class="text-1"
            name="password-confirmation"
            :disabled="session.isPending"
            type="password"
            autocomplete="new-password"
            aria-label="Повторите пароль"
            placeholder="Повторите пароль"
            required
            :aria-invalid="!!errors.confirmation"
            :aria-describedby="errors.confirmation ? 'confirmation-error' : undefined"
            @input="clearError('confirmation')"
          />
        </label>
        <p
          v-if="errors.confirmation"
          id="confirmation-error"
          class="text-4 login-form__error"
          role="alert"
        >
          {{ errors.confirmation }}
        </p>
      </div>
    </div>
    <a
      v-if="mode === 'login'"
      class="text-2 login-form__forgot"
      aria-disabled="true"
      role="link"
      title="Восстановление пароля будет доступно позже"
      >Забыли пароль?</a
    >
    <div class="login-form__bottom">
      <label class="login-form__remember text-2" v-if="mode === 'login'"
        ><input
          v-model="remember"
          type="checkbox"
          name="remember"
          :disabled="session.isPending"
        />Запомнить меня</label
      >
      <p v-if="status" class="login-form__status text-4" :role="isError ? 'alert' : 'status'">
        {{ status }}
      </p>
      <BaseButton
        class="login-form__submit"
        type="submit"
        :loading="session.isPending"
        :disabled="session.isInitializing"
        full-width
        >{{ mode === 'register' ? 'Зарегистрироваться' : 'Войти' }}</BaseButton
      >
    </div>
  </form>
</template>

<style scoped>
.login-form {
  display: flex;
  flex-direction: column;
  flex: 1;
  margin-top: 10px;
}
.login-form__fields {
  display: flex;
  flex-direction: column;
  gap: 32px;
}
.login-form--register {
  margin-top: 100px;
}
.login-form__field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.login-form__input-wrap {
  display: flex;
  align-items: center;
  gap: 15px;
  min-height: 75px;
  padding: 0 17px;
  border-radius: var(--border-radius-md);
  background: var(--color-auth-input);
}
.login-form__input-wrap:focus-within {
  outline: 2px solid var(--color-yellow);
  outline-offset: 2px;
}
.login-form__input-wrap svg {
  flex-shrink: 0;
}
.login-form__input-wrap input {
  min-width: 0;
  width: 100%;
  padding: 12px 0;
  border: 0;
  outline: none;
  background: transparent;
  color: var(--color-text-primary);
  font-weight: var(--font-weight-semibold);
  line-height: 1.2;
}
.login-form__input-wrap input::placeholder {
  color: var(--color-text-primary);
  opacity: 1;
}
.login-form__forgot {
  align-self: flex-end;
  margin-top: 10px;
  color: var(--color-yellow);
  text-decoration: none;
  cursor: not-allowed;
  line-height: 35px;
}
.login-form__bottom {
  display: flex;
  flex-direction: column;
  gap: 37px;
  margin-top: auto;
  padding-top: 32px;
}
.login-form__remember {
  display: flex;
  align-items: center;
  gap: 23px;
  color: var(--color-text-secondary);
  cursor: pointer;
  line-height: 35px;
}
.login-form__remember input {
  appearance: none;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  flex-shrink: 0;
  margin: 0;
  border: 2px solid var(--color-yellow);
  border-radius: 5px;
  cursor: pointer;
}
.login-form__remember input:checked {
  background: var(--color-yellow);
}
.login-form__remember input:checked::after {
  content: '✓';
  color: var(--color-background);
  font-size: var(--font-size-text-4);
}
.login-form__submit {
  min-height: 74px;
  border-radius: var(--border-radius-md);
  font-size: var(--font-size-text-1);
  color: var(--color-auth-surface);
}
.login-form__error,
.login-form__status {
  color: var(--color-yellow);
}
</style>
