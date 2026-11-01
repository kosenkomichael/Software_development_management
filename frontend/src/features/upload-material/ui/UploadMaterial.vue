<script setup lang="ts">
import { onBeforeUnmount, ref } from 'vue'
import { ArrowRight, Sparkles, UploadCloud } from 'lucide-vue-next'
import { createMaterialApi, formatSize, type Material } from '@/entities/material'
import { useSessionStore } from '@/entities/session'
import { BaseButton } from '@/shared/ui/button'
import { designAssets } from '@/shared/assets'
const emit = defineEmits<{ uploaded: [material: Material] }>()
const api = createMaterialApi(useSessionStore().request)
const fileInput = ref<HTMLInputElement>()
const selected = ref<File | null>(null)
const error = ref('')
const uploading = ref(false)
const dragging = ref(false)
let controller: AbortController | null = null
const mimeTypes: Record<string, string> = {
  pdf: 'application/pdf',
  docx: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  pptx: 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
}
function choose(file?: File) {
  if (!file || uploading.value) return
  error.value = ''
  const extension = file.name.split('.').pop()?.toLowerCase() ?? ''
  if (!mimeTypes[extension]) {
    error.value = 'Выберите файл PDF, DOCX или PPTX.'
    selected.value = null
    return
  }
  if (!file.size || file.size > 50 * 1024 * 1024) {
    error.value = 'Файл должен быть непустым и не превышать 50 МБ.'
    selected.value = null
    return
  }
  selected.value = new File([file], file.name, { type: mimeTypes[extension] })
}
function onFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  choose(input.files?.[0])
  input.value = ''
}
function drop(event: DragEvent) {
  dragging.value = false
  choose(event.dataTransfer?.files[0])
}
async function upload() {
  if (!selected.value || uploading.value) return
  uploading.value = true
  error.value = ''
  controller = new AbortController()
  const timeout = setTimeout(() => controller?.abort(), 120000)
  try {
    emit('uploaded', await api.upload(selected.value, controller.signal))
  } catch (reason) {
    error.value = controller.signal.aborted
      ? 'Загрузка остановлена или заняла слишком много времени. Попробуйте ещё раз.'
      : reason instanceof Error
        ? reason.message
        : 'Не удалось загрузить файл.'
  } finally {
    clearTimeout(timeout)
    uploading.value = false
  }
}
onBeforeUnmount(() => controller?.abort())
</script>

<template>
  <form class="upload-material-form" @submit.prevent="upload">
    <section
      class="surface upload-material"
      :class="{ 'upload-material--dragging': dragging }"
      :style="{ '--upload-background': `url(${designAssets.uploadBackground})` }"
      @dragover.prevent="dragging = true"
      @dragleave.prevent="dragging = false"
      @drop.prevent="drop"
    >
      <div class="upload-material__dropzone" :aria-busy="uploading">
        <div class="upload-material__icon">
          <UploadCloud :size="56" :stroke-width="1.5" aria-hidden="true" />
        </div>
        <h2 class="text-1">{{ selected ? selected.name : 'Перетащите файл сюда' }}</h2>
        <p class="text-3 muted">
          {{ selected ? formatSize(selected.size) : 'или выберите на устройстве' }}
        </p>
        <input
          ref="fileInput"
          class="sr-only"
          type="file"
          accept=".pdf,.docx,.pptx"
          tabindex="-1"
          @change="onFileChange"
        />
        <div class="upload-material__actions">
          <BaseButton size="small" :disabled="uploading" @click="fileInput?.click()">{{
            selected ? 'Выбрать другой файл' : 'Выбрать файл'
          }}</BaseButton>
        </div>
        <p v-if="error" class="text-3 danger" role="alert">{{ error }}</p>
        <p v-if="uploading" class="text-3 accent" role="status">
          Загружаем файл… После загрузки начнётся обработка.
        </p>
        <div class="upload-material__formats text-3 muted">
          <p>Поддерживаемые форматы: PDF, DOCX, PPTX</p>
          <p>Максимальный размер файла: 50 МБ</p>
        </div>
      </div>
    </section>
    <BaseButton
      class="upload-material__submit"
      type="submit"
      full-width
      :disabled="!selected"
      :loading="uploading"
    >
      <template #icon-left><Sparkles :size="24" aria-hidden="true" /></template>
      {{ uploading ? 'Создаём материал…' : 'Создать материал' }}
      <template #icon-right><ArrowRight :size="24" aria-hidden="true" /></template>
    </BaseButton>
  </form>
</template>

<style scoped>
.upload-material-form {
  display: flex;
  flex-direction: column;
  gap: 24px;
}
.upload-material {
  min-height: 460px;
  padding: 20px;
  border-radius: var(--radius-panel);
  background-image:
    linear-gradient(
      120deg,
      color-mix(in srgb, var(--color-panel) 45%, transparent),
      color-mix(in srgb, var(--color-panel) 15%, transparent)
    ),
    var(--upload-background);
  background-size: cover;
  background-position: center;
}
.upload-material__dropzone {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 14px;
  min-height: 416px;
  padding: 36px 24px;
  border: 1px dashed color-mix(in srgb, var(--color-yellow) 65%, transparent);
  border-radius: var(--border-radius-md);
  text-align: center;
}
.upload-material--dragging .upload-material__dropzone {
  border-color: var(--color-yellow);
  background: var(--color-active);
}
.upload-material__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 96px;
  height: 96px;
  margin-bottom: 8px;
  border: 1px solid color-mix(in srgb, var(--color-yellow) 12%, transparent);
  border-radius: 50%;
  background: radial-gradient(
    circle,
    color-mix(in srgb, var(--color-orange) 28%, transparent),
    color-mix(in srgb, var(--color-orange) 8%, transparent)
  );
  box-shadow: 0 0 32px color-mix(in srgb, var(--color-orange) 10%, transparent);
  color: var(--color-yellow);
}
.upload-material__actions {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  margin: 12px 0;
}
.upload-material__formats {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: var(--font-size-text-4);
}
.upload-material__submit {
  min-height: 74px;
  border-radius: var(--border-radius-md);
  font-size: var(--font-size-text-2);
  box-shadow: 0 6px 24px color-mix(in srgb, var(--color-yellow) 12%, transparent);
}
.upload-material__submit:disabled:not([aria-busy='true']) {
  opacity: 0.7;
}
</style>
