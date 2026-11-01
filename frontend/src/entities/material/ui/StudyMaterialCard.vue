<script setup lang="ts">
import { FileText, MoreHorizontal, Heart } from 'lucide-vue-next'
import { materialStatusLabel, formatSize, type Material } from '../model/types'
defineProps<{ material: Material; demo?: boolean; author?: string }>()
defineEmits<{ open: []; quiz: []; details: [] }>()
</script>

<template>
  <article class="surface study-card">
    <div class="study-card__top">
      <button class="study-card__title text-1" type="button" @click="$emit('open')">
        {{ material.original_filename }}
      </button>
      <button
        v-if="demo"
        class="icon-button"
        type="button"
        aria-label="Об избранном"
        @click="$emit('details')"
      >
        <Heart :size="28" />
      </button>
      <button
        v-else
        class="icon-button"
        type="button"
        aria-label="Информация о материале"
        @click="$emit('details')"
      >
        <MoreHorizontal :size="28" />
      </button>
    </div>
    <p class="text-3 muted">
      {{ author || `${formatSize(material.size_bytes)} · ${materialStatusLabel[material.status]}` }}
    </p>
    <div class="study-card__actions">
      <button
        class="study-card__pill study-card__pill--notes text-3"
        type="button"
        @click="$emit('open')"
      >
        Конспект
      </button>
      <button
        class="study-card__pill study-card__pill--quiz text-3"
        type="button"
        @click="$emit('quiz')"
      >
        Тест
      </button>
      <FileText
        v-if="material.status === 'processing'"
        class="accent"
        :size="22"
        aria-label="Обработка"
      />
    </div>
  </article>
</template>

<style scoped>
.study-card {
  display: flex;
  flex-direction: column;
  min-width: 0;
  padding: 18px 20px;
  min-height: 193px;
  border-radius: var(--radius-card);
}
.study-card__top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 8px;
}
.study-card__title {
  min-width: 0;
  padding: 0;
  border: 0;
  background: transparent;
  color: var(--color-text-primary);
  text-align: left;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.study-card__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-top: auto;
  padding-top: 28px;
}
.study-card__pill {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 12px 16px;
  min-height: 58px;
  border: 0;
  border-radius: var(--radius-card);
  color: var(--color-text-primary);
}
.study-card__pill--notes {
  background: var(--color-orange);
}
.study-card__pill--quiz {
  background: var(--color-green);
}
</style>
