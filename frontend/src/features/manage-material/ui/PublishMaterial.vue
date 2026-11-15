<script setup lang="ts">
import { onBeforeUnmount, ref, watch } from 'vue'
import { createPublicMaterialApi } from '@/entities/material'
import { useSessionStore } from '@/entities/session'
import { BaseButton } from '@/shared/ui/button'
const props = defineProps<{ materialId: string }>()
const api = createPublicMaterialApi(useSessionStore().request)
const published = ref(false)
const title = ref('')
const editing = ref(false)
const pending = ref(false)
const error = ref('')
let controller = new AbortController()
watch(() => props.materialId, async (id) => {
  controller.abort(); controller = new AbortController()
  const signal = controller.signal
  error.value = ''; pending.value = true; editing.value = false
  try { const state = await api.publication(id, signal); if (!signal.aborted) { published.value = state.is_public; title.value = state.title } }
  catch (reason) { if (!signal.aborted) error.value = reason instanceof Error ? reason.message : 'Не удалось получить статус публикации.' }
  finally { if (!signal.aborted) pending.value = false }
}, { immediate: true })
async function save(publish = !published.value) {
  if (pending.value) return
  pending.value = true; error.value = ''
  const signal = controller.signal
  try {
    const state = await api.publish(props.materialId, { is_public: publish, title: title.value.trim() })
    if (!signal.aborted) { published.value = state.is_public; editing.value = false }
  } catch (reason) { if (!signal.aborted) error.value = reason instanceof Error ? reason.message : 'Не удалось изменить публикацию.' }
  finally { if (!signal.aborted) pending.value = false }
}
onBeforeUnmount(() => controller.abort())
</script>
<template>
  <div class="publication">
    <div class="publication__actions">
      <BaseButton variant="transparent" :disabled="pending" @click="editing = !editing">{{ published ? 'Настройки публикации' : 'Опубликовать материал' }}</BaseButton>
      <RouterLink v-if="published" class="text-link text-3" :to="`/community/materials/${materialId}`">Открыть в сообществе</RouterLink>
    </div>
    <form v-if="editing" class="notice publication" @submit.prevent="save(true)">
      <div>
        <label class="app-field text-3">Название материала в сообществе<input v-model="title" class="app-input" maxlength="200" required :disabled="pending" /></label>
        <p v-if="!published" class="text-3 muted">Будут доступны исходная лекция, конспект и готовый тест, если он есть. Другие пользователи смогут сохранить независимую копию в свою библиотеку. Личные результаты прохождений не публикуются.</p>
      </div>
      <p v-if="published" class="text-3 muted">Кнопка «Обновить пакет» добавит последний готовый тест. При снятии с публикации материал исчезнет из сообщества. Уже сохранённые копии и результаты участников останутся у них.</p>
      <div class="publication__actions">
        <BaseButton type="submit" :loading="pending" :disabled="!title.trim()">{{ published ? 'Обновить пакет' : 'Опубликовать' }}</BaseButton>
        <BaseButton v-if="published" variant="transparent" :disabled="pending" @click="save(false)">Снять с публикации</BaseButton>
        <BaseButton variant="transparent" :disabled="pending" @click="editing = false">Отмена</BaseButton>
      </div>
    </form>
    <p v-if="error" class="text-3 danger" role="alert">{{ error }}</p>
  </div>
</template>
<style scoped>
.publication { display: flex; flex-direction: column; gap: 16px; }
.publication__actions { display: flex; align-items: center; flex-wrap: wrap; gap: 16px; }
</style>
