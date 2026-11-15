export { default as GenerationWait } from './GenerationWait.vue'

export function clearGenerationWait(storageKey: string) {
  try {
    sessionStorage.removeItem(storageKey)
  } catch { /* Browser storage may be unavailable. */ }
}
