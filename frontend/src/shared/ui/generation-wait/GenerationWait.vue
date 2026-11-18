<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'

const props = defineProps<{ storageKey: string }>()
const now = ref(Date.now())
const startedAt = ref(now.value)
watch(() => props.storageKey, (key) => {
  const current = Date.now()
  startedAt.value = current
  try {
    const stored = Number(sessionStorage.getItem(key))
    if (stored > 0 && stored <= current) startedAt.value = stored
    else sessionStorage.setItem(key, String(current))
  } catch { /* The timer also works without browser storage. */ }
  now.value = current
}, { immediate: true })
const seconds = computed(() => Math.max(0, Math.floor((now.value - startedAt.value) / 1000)))
const elapsed = computed(() => {
  const minutes = Math.floor(seconds.value / 60)
  return `${String(minutes).padStart(2, '0')}:${String(seconds.value % 60).padStart(2, '0')}`
})
const clock = setInterval(() => { now.value = Date.now() }, 1000)
onBeforeUnmount(() => clearInterval(clock))
</script>

<template>
  <div class="generation-wait">
    <div class="generation-wait__timer" aria-live="off">
      <span class="text-3 muted">Время ожидания</span>
      <span class="generation-wait__elapsed title-3">{{ elapsed }}</span>
    </div>
    <div class="generation-wait__activity" aria-hidden="true"><span /></div>
    <p class="text-3 muted">
      {{ seconds >= 300
        ? 'Обработка занимает больше времени. Мы продолжаем проверять результат.'
        : 'Это может занять несколько минут. Время зависит от объёма лекции и скорости генерации.' }}
    </p>
    <p class="text-3 muted">Точное время до готовности пока неизвестно.</p>
  </div>
</template>

<style scoped>
.generation-wait { display: flex; flex-direction: column; align-items: center; gap: 12px; width: min(100%, 520px); }
.generation-wait__timer { display: flex; flex-direction: column; align-items: center; gap: 6px; }
.generation-wait__elapsed { font-variant-numeric: tabular-nums; color: var(--color-yellow); }
.generation-wait__activity { width: 100%; height: 5px; border-radius: 8px; overflow: hidden; background: var(--color-panel-border); }
.generation-wait__activity span { display: block; width: 35%; height: 100%; border-radius: inherit; background: var(--color-yellow); animation: generation-activity 2s ease-in-out infinite alternate; }
@keyframes generation-activity { from { transform: translateX(-100%); } to { transform: translateX(290%); } }
@media (prefers-reduced-motion: reduce) { .generation-wait__activity span { animation: none; width: 100%; opacity: .6; } }
</style>
