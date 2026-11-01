<script setup lang="ts">
import { useRouter } from 'vue-router'
import { designAssets } from '@/shared/assets'

const router = useRouter()
function showExample(index = 0) {
  void router.push({ name: 'demo', query: index ? { tab: 'quiz' } : {} })
}
</script>

<template>
  <section class="result-example__example">
    <h2 class="title-1">Пример результата</h2>
    <button
      class="result-example__preview"
      type="button"
      aria-label="Открыть пример конспекта и теста"
      @click="showExample()"
    >
      <img
        :src="designAssets.resultPreview"
        alt="Пример конспекта по нейронным сетям с разделами, определениями и тестом"
      />
    </button>
  </section>
</template>

<style scoped>
.result-example__preview {
  display: block;
  width: 100%;
  margin-top: 80px;
  padding: 0;
  border: 0;
  border-radius: var(--radius-panel);
  background: var(--color-panel);
  overflow: hidden;
}
.result-example__preview img {
  width: 100%;
  height: auto;
}
</style>
