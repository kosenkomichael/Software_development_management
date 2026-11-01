<script setup lang="ts">
import { useRouter } from 'vue-router'
import { StudyMaterialCard, type Material } from '@/entities/material'

const router = useRouter()
const examples: Material[] = [
  'Основы нейронных сетей',
  'Функции активации',
  'Обучение нейронной сети',
].map((name, index) => ({
  id: `example-${index}`,
  original_filename: name,
  content_type: 'application/pdf',
  size_bytes: 12 * 1024 * 1024,
  status: 'done',
  created_at: '',
}))
function showExample(index = 0) {
  void router.push({ name: 'demo', query: index ? { tab: 'quiz' } : {} })
}
</script>

<template>
  <section class="community__community">
    <header class="section-heading">
      <h2 class="title-1">Учись вместе с другими</h2>
      <span class="text-4 muted">Примеры материалов</span>
    </header>
    <div class="community__examples">
      <StudyMaterialCard
        v-for="item in examples"
        :key="item.id"
        :material="item"
        demo
        author="Демонстрационный материал"
        @open="showExample()"
        @quiz="showExample(1)"
        @details="router.push('/community')"
      />
    </div>
  </section>
</template>

<style scoped>
.community__examples {
  display: flex;
  gap: 28px;
  margin-top: 40px;
}
.community__examples > * {
  flex: 0 1 438px;
}
</style>
