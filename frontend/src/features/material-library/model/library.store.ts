import { computed, ref, watch } from 'vue'
import { defineStore } from 'pinia'
import { useSessionStore } from '@/entities/session'
import { createMaterialApi, type Material } from '@/entities/material'

export const useMaterialLibraryStore = defineStore('material-library', () => {
  const session = useSessionStore()
  const api = createMaterialApi(session.request)
  const items = ref<Material[]>([])
  const quizReady = ref<Record<string, boolean>>({})
  const loading = ref(false)
  const error = ref('')
  const loaded = ref(false)
  const total = ref(0)
  const bytes = computed(() => items.value.reduce((sum, item) => sum + item.size_bytes, 0))
  let version = 0
  let pending: Promise<void> | null = null
  async function load(force = false) {
    if (pending) return pending
    if (!session.isAuthenticated || (loaded.value && !force)) return
    const revision = version
    const owner = session.user?.id
    loading.value = true
    error.value = ''
    const operation = (async () => {
      try {
        const first = await api.list()
        const all = [...first.items]
        for (let page = 2; all.length < first.total; page++) {
          const next = await api.list(page)
          if (!next.items.length) break
          all.push(...next.items)
        }
        if (revision !== version || owner !== session.user?.id) return
        items.value = all
        total.value = first.total
        loaded.value = true
      } catch (reason) {
        if (revision === version)
          error.value = reason instanceof Error ? reason.message : 'Не удалось загрузить материалы.'
      } finally {
        if (revision === version) loading.value = false
      }
    })()
    const tracked: Promise<void> = operation.finally(() => {
      if (pending === tracked) pending = null
    })
    pending = tracked
    return pending
  }
  async function loadQuizStatuses() {
    const revision = version
    const done = items.value.filter((item) => item.status === 'done')
    for (let index = 0; index < done.length; index += 6) {
      const chunk = done.slice(index, index + 6)
      await Promise.all(
        chunk.map(async (item) => {
          try {
            const result = await api.quizStatus(item.id)
            if (revision === version)
              quizReady.value[item.id] = !!result.quiz_id && result.status === 'done'
          } catch {
            /* Leave unavailable statuses unknown; do not invent a count. */
          }
        })
      )
    }
  }
  function upsert(item: Material) {
    const index = items.value.findIndex((current) => current.id === item.id)
    if (index === -1) {
      items.value.unshift(item)
      total.value++
    } else items.value[index] = item
  }
  watch(
    () => session.user?.id,
    () => {
      version++
      pending = null
      items.value = []
      total.value = 0
      quizReady.value = {}
      loaded.value = false
      loading.value = false
      error.value = ''
    }
  )
  return { items, total, bytes, quizReady, loading, error, loaded, load, loadQuizStatuses, upsert }
})
