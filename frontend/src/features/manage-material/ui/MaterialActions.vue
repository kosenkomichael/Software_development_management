<script setup lang="ts">
import { onBeforeUnmount, ref } from 'vue'
import { Pencil, Star, Trash2 } from 'lucide-vue-next'
import { useSessionStore } from '@/entities/session'
import { createMaterialApi, type Material } from '@/entities/material'
import { BaseButton } from '@/shared/ui/button'
const props = defineProps<{ material: Material }>()
const emit = defineEmits<{ updated: [material: Material]; deleted: [] }>()
const api = createMaterialApi(useSessionStore().request)
const mode = ref<'rename' | 'delete' | null>(null)
const name = ref('')
const pending = ref(false)
const error = ref('')
let disposed = false
onBeforeUnmount(() => { disposed = true })
function rename() { name.value = props.material.original_filename; error.value = ''; mode.value = 'rename' }
async function update(change: { original_filename?: string; is_favorite?: boolean }) {
  if (pending.value) return
  pending.value = true
  error.value = ''
  try {
    const updated = await api.update(props.material.id, change)
    if (!disposed) {
      emit('updated', { ...updated, download_url: props.material.download_url })
      mode.value = null
    }
  } catch (reason) {
    if (!disposed) error.value = reason instanceof Error ? reason.message : 'Не удалось сохранить изменения.'
  } finally { if (!disposed) pending.value = false }
}
async function remove() {
  if (pending.value) return
  pending.value = true
  error.value = ''
  try {
    await api.remove(props.material.id)
    if (!disposed) emit('deleted')
  } catch (reason) {
    if (!disposed) error.value = reason instanceof Error ? reason.message : 'Не удалось удалить материал.'
  } finally { if (!disposed) pending.value = false }
}
</script>
<template>
  <div class="material-actions">
    <div class="material-actions__buttons">
      <BaseButton variant="transparent" :disabled="pending" :aria-pressed="!!material.is_favorite" @click="update({ is_favorite: !material.is_favorite })">
        <template #icon-left><Star :fill="material.is_favorite ? 'currentColor' : 'none'" /></template>
        {{ material.is_favorite ? 'Убрать из избранного' : 'В избранное' }}
      </BaseButton>
      <BaseButton variant="transparent" :disabled="pending" @click="rename"><template #icon-left><Pencil /></template>Переименовать</BaseButton>
      <BaseButton variant="transparent" :disabled="pending" @click="mode = 'delete'; error = ''"><template #icon-left><Trash2 /></template>Удалить</BaseButton>
    </div>
    <form v-if="mode === 'rename'" class="material-actions__form" @submit.prevent="update({ original_filename: name.trim() })">
      <label class="app-field text-3">Название материала<input v-model="name" class="app-input" maxlength="255" required :disabled="pending" /></label>
      <div class="material-actions__buttons"><BaseButton type="submit" :loading="pending" :disabled="!name.trim()">Сохранить</BaseButton><BaseButton variant="transparent" :disabled="pending" @click="mode = null">Отмена</BaseButton></div>
    </form>
    <div v-if="mode === 'delete'" class="notice material-actions__form">
      <p class="text-2">Удалить «{{ material.original_filename }}» из библиотеки?</p>
      <p class="text-3 muted">Материал, конспект, тесты и история прохождений станут недоступны.</p>
      <div class="material-actions__buttons"><BaseButton :loading="pending" @click="remove">Удалить материал</BaseButton><BaseButton variant="transparent" :disabled="pending" @click="mode = null">Отмена</BaseButton></div>
    </div>
    <p v-if="error" class="text-3 danger" role="alert">{{ error }}</p>
  </div>
</template>
<style scoped>
.material-actions, .material-actions__form { display: flex; flex-direction: column; gap: 16px; }
.material-actions__buttons { display: flex; flex-wrap: wrap; gap: 12px; }
</style>
