<script setup lang="ts">
import { reactive, ref, watch } from 'vue'
import { BaseModal } from '@/shared/ui/modal'
import { BaseButton } from '@/shared/ui/button'
const props = defineProps<{ open: boolean }>()
const emit = defineEmits<{ close: [] }>()
const form = reactive({ current: '', password: '', confirmation: '' })
const error = ref('')
watch(
  () => props.open,
  () => {
    form.current = ''
    form.password = ''
    form.confirmation = ''
    error.value = ''
  }
)
function validate() {
  if (!form.current || !form.password || !form.confirmation) error.value = 'Заполните все поля.'
  else if (form.password.length < 8 || form.password.length > 128)
    error.value = 'Пароль должен содержать от 8 до 128 символов.'
  else if (form.password !== form.confirmation) error.value = 'Новые пароли не совпадают.'
  else error.value = ''
}
</script>
<template>
  <BaseModal :open="open" labelledby="password-title" @close="emit('close')"
    ><form class="password-modal" @submit.prevent="validate">
      <h2 id="password-title" class="title-3">Сброс пароля</h2>
      <label class="app-field text-2"
        >Введите старый пароль<input
          v-model="form.current"
          data-modal-autofocus
          class="app-input text-1"
          type="password"
          autocomplete="current-password"
          required
          @blur="form.current && validate()" /></label
      ><label class="app-field text-2"
        >Введите новый пароль<input
          v-model="form.password"
          class="app-input text-1"
          type="password"
          autocomplete="new-password"
          required
          @blur="form.password && validate()" /></label
      ><label class="app-field text-2"
        >Повторите новый пароль<input
          v-model="form.confirmation"
          class="app-input text-1"
          type="password"
          autocomplete="new-password"
          required
          @blur="form.confirmation && validate()"
      /></label>
      <p v-if="error" class="text-3 danger" role="alert">{{ error }}</p>
      <p class="notice text-3">Смена пароля пока недоступна.</p>
      <div class="password-modal__actions">
        <BaseButton variant="transparent" @click="emit('close')">Отмена</BaseButton
        ><BaseButton type="submit" disabled title="Смена пароля пока недоступна"
          >Сохранить</BaseButton
        >
      </div>
    </form></BaseModal
  >
</template>
<style scoped>
.password-modal {
  display: flex;
  flex-direction: column;
  gap: 32px;
  width: 734px;
  padding: 40px 63px 28px;
}
.password-modal .app-input {
  background: var(--color-panel);
  min-height: 75px;
}
.password-modal__actions {
  display: flex;
  justify-content: flex-end;
  gap: 22px;
}
.password-modal__actions :deep(.base-button) {
  min-width: 180px;
  border-radius: var(--border-radius-md);
}
</style>
