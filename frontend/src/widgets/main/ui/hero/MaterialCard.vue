<script setup lang="ts">
import { File } from 'lucide-vue-next'

interface Props {
  fileName: string
  pages: number
  fileSize: string
}

defineProps<Props>()
</script>

<template>
  <div class="material-card">
    <File class="material-card__icon" :size="32" :stroke-width="1.7" aria-hidden="true" />

    <div class="material-card__content">
      <p class="material-card__name" :title="fileName">
        {{ fileName }}
      </p>

      <p class="material-card__details">{{ pages }} страниц · {{ fileSize }}</p>
    </div>
  </div>
</template>

<style scoped>
.material-card {
  display: flex;
  align-items: center;
  gap: 24px;
  width: 100%;
  min-height: 128px;
  padding: 24px;
  background-color: rgba(48, 45, 50, 0.85);
  border: 2px solid rgba(255, 255, 255, 0.08);
  border-radius: 30px;
  backdrop-filter: blur(12px);
}
.material-card__icon {
  flex-shrink: 0;
  width: 56px;
  height: 64px;
  color: var(--color-text-primary);
}
.material-card__content {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 0;
}
.material-card__name {
  overflow: hidden;
  color: var(--color-text-primary);
  font-size: 20px;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.material-card__details {
  color: var(--color-text-secondary);
  font-size: 20px;
}
@media (max-width: 1400px) {
  .material-card {
    gap: 16px;
    padding: 20px;
    min-height: 108px;
  }
  .material-card__icon {
    width: 40px;
    height: 48px;
  }
  .material-card__name,
  .material-card__details {
    font-size: 16px;
  }
}
</style>
