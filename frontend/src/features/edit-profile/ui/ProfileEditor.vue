<script setup lang="ts">
import { ref, watch } from 'vue'
import { Pencil } from 'lucide-vue-next'
import { useSessionStore } from '@/entities/session'
import { BaseModal } from '@/shared/ui/modal'
import { BaseButton } from '@/shared/ui/button'
import { designAssets } from '@/shared/assets'
import ChangePasswordModal from './ChangePasswordModal.vue'
const props = defineProps<{ open: boolean }>()
const emit = defineEmits<{ close: [] }>()
const session = useSessionStore()
const firstName = ref('')
const lastName = ref('')
const email = ref('')
const passwordOpen = ref(false)
watch(
  () => props.open,
  () => {
    firstName.value = ''
    lastName.value = ''
    email.value = session.user?.email ?? ''
    passwordOpen.value = false
  }
)
</script>
<template>
  <BaseModal :open="open" labelledby="profile-edit-title" @close="emit('close')"
    ><div
      class="profile-editor"
      :style="{ backgroundImage: `url(${designAssets.uploadBackground})` }"
    >
      <header class="profile-editor__identity">
        <img :src="designAssets.editAvatar" alt="" width="120" height="120" />
        <div>
          <h2 id="profile-edit-title" class="title-4">Редактирование профиля</h2>
          <p class="text-2 muted">{{ session.user?.email }}</p>
        </div>
      </header>
      <form class="profile-editor__form" @submit.prevent>
        <div class="profile-editor__fields">
          <label class="app-field text-2"
            >Фамилия<input
              v-model="lastName"
              class="app-input text-1"
              data-modal-autofocus
              name="family-name"
              autocomplete="family-name"
              placeholder="Фамилия" /></label
          ><label class="app-field text-2"
            >Имя<input
              v-model="firstName"
              class="app-input text-1"
              name="given-name"
              autocomplete="given-name"
              placeholder="Имя" /></label
          ><label class="app-field text-2"
            >Email<input
              v-model="email"
              class="app-input text-1"
              type="email"
              autocomplete="email"
              placeholder="Email"
          /></label>
          <div class="app-field text-2">
            <span>Пароль</span
            ><button
              class="app-input profile-editor__password text-1"
              type="button"
              @click="passwordOpen = true"
            >
              <span aria-hidden="true">********************</span
              ><span class="sr-only">Открыть смену пароля</span><Pencil :size="28" />
            </button>
          </div>
        </div>
        <p class="notice text-3">Сохранение имени и данных профиля пока недоступно.</p>
        <div class="profile-editor__actions">
          <BaseButton variant="transparent" @click="emit('close')">Отмена</BaseButton
          ><BaseButton type="submit" disabled title="Редактирование профиля пока недоступно"
            >Сохранить</BaseButton
          >
        </div>
      </form>
    </div></BaseModal
  ><ChangePasswordModal :open="open && passwordOpen" @close="passwordOpen = false" />
</template>
<style scoped>
.profile-editor {
  display: flex;
  flex-direction: column;
  gap: 26px;
  width: min(1365px, calc(100vw - 64px));
  padding: 42px 56px;
  background-size: cover;
  background-position: center;
}
.profile-editor__identity {
  display: flex;
  align-items: center;
  gap: 36px;
}
.profile-editor__form {
  display: flex;
  flex-direction: column;
  gap: 24px;
}
.profile-editor__fields {
  display: flex;
  flex-wrap: wrap;
  gap: 16px 64px;
}
.profile-editor__fields > * {
  flex: 0 0 calc((100% - 64px) / 2);
}
.profile-editor .app-input {
  min-height: 75px;
}
.profile-editor__password {
  display: flex;
  align-items: center;
  justify-content: space-between;
  text-align: left;
}
.profile-editor__actions {
  display: flex;
  justify-content: flex-end;
  gap: 24px;
}
.profile-editor__actions :deep(.base-button) {
  min-width: 200px;
  border-radius: var(--border-radius-md);
}
@media (max-width: 768px) {
  .profile-editor {
    width: min(1365px, calc(100vw - 24px));
    padding: 24px 16px;
  }
  .profile-editor__identity {
    flex-wrap: wrap;
    gap: 16px;
  }
  .profile-editor__identity img {
    width: 84px;
    height: 84px;
  }
  .profile-editor__fields > * {
    flex: 1 1 100%;
  }
  .profile-editor .app-input {
    min-height: 56px;
  }
  .profile-editor__password {
    flex-wrap: wrap;
  }
  .profile-editor__actions {
    flex-wrap: wrap;
  }
  .profile-editor__actions :deep(.base-button) {
    min-width: 0;
    flex: 1;
  }
}
</style>
