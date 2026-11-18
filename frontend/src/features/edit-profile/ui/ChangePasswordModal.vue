<script setup lang="ts">
import { reactive, ref, watch } from 'vue'
import { useSessionStore } from '@/entities/session'
import { BaseModal } from '@/shared/ui/modal'
import { BaseButton } from '@/shared/ui/button'
const props = defineProps<{ open: boolean }>()
const emit = defineEmits<{ close: []; changed: [] }>()
const session = useSessionStore()
function close() { if (!session.isPending) emit('close') }
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
async function save() {
  if (session.isPending) return
  validate()
  if (error.value) return
  try {
    await session.changePassword(form.current, form.password)
    form.current = ''; form.password = ''; form.confirmation = ''
    emit('changed')
  } catch (reason) { error.value = reason instanceof Error ? reason.message : 'Не удалось изменить пароль.' }
}
</script>
<template>
  <BaseModal :open="open" labelledby="password-title" @close="close"
    ><form class="password-modal" @submit.prevent="save">
      <h2 id="password-title" class="title-3">Смена пароля</h2>
      <label class="app-field text-2"
        >Введите старый пароль<input
          v-model="form.current"
          data-modal-autofocus
          class="app-input text-1"
          type="password"
          autocomplete="current-password"
          required
          maxlength="128"
          :disabled="session.isPending"
          @blur="form.current && validate()" /></label
      ><label class="app-field text-2"
        >Введите новый пароль<input
          v-model="form.password"
          class="app-input text-1"
          type="password"
          autocomplete="new-password"
          required
          maxlength="128"
          :disabled="session.isPending"
          @blur="form.password && validate()" /></label
      ><label class="app-field text-2"
        >Повторите новый пароль<input
          v-model="form.confirmation"
          class="app-input text-1"
          type="password"
          autocomplete="new-password"
          required
          maxlength="128"
          :disabled="session.isPending"
          @blur="form.confirmation && validate()"
      /></label>
      <p v-if="error" class="text-3 danger" role="alert">{{ error }}</p>
      <p class="notice text-3">После смены пароля другие устройства выйдут из аккаунта.</p>
      <div class="password-modal__actions">
        <BaseButton variant="transparent" :disabled="session.isPending" @click="close">Отмена</BaseButton
        ><BaseButton type="submit" :loading="session.isPending"
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
@media (max-width: 768px) {
  .password-modal {
    width: min(734px, 100%);
    padding: 24px 16px;
  }
  .password-modal__actions {
    flex-wrap: wrap;
  }
  .password-modal__actions :deep(.base-button) {
    min-width: 0;
    flex: 1;
  }
}
</style>
