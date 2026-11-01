<script setup lang="ts">
import { useRouter } from 'vue-router'
import { MaterialProgress } from '@/widgets/material-progress'
import { UploadMaterial } from '@/features/upload-material'
import type { Material } from '@/entities/material'
const router = useRouter()
function uploaded(material: Material) {
  void router.push({ name: 'material-processing', params: { id: material.id } })
}
</script>
<template>
  <div class="workspace-page create-material-page">
    <header class="page-heading">
      <h1 class="title-2">Создать материал</h1>
      <p class="text-2 muted">Загрузите лекцию, чтобы получить конспект и тест</p>
    </header>
    <MaterialProgress :step="1" compact />
    <UploadMaterial @uploaded="uploaded" />
  </div>
</template>

<style scoped>
.create-material-page {
  gap: 24px;
}
</style>
