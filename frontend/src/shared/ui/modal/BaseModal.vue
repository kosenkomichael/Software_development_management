<script lang="ts">
let openModalCount = 0
let originalBodyOverflow = ''
</script>
<script setup lang="ts">
import { onBeforeUnmount, ref, watch } from 'vue'
import { X } from 'lucide-vue-next'

defineOptions({ inheritAttrs: false })

const props = defineProps<{ open: boolean; labelledby: string }>()
const emit = defineEmits<{ close: [] }>()
const dialog = ref<HTMLDialogElement>()
let previousFocus: HTMLElement | null = null
let hasScrollLock = false
const pointerStartedOnBackdrop = ref(false)

function onClose() {
  restore()
  if (props.open) emit('close')
}

function restore() {
  if (hasScrollLock) {
    hasScrollLock = false
    openModalCount = Math.max(0, openModalCount - 1)
    if (!openModalCount) document.body.style.overflow = originalBodyOverflow
  }
  if (previousFocus?.isConnected) previousFocus.focus()
  previousFocus = null
}

watch(
  [() => props.open, dialog],
  ([open, element]) => {
    if (!element) return
    if (open && !element.open) {
      previousFocus = document.activeElement instanceof HTMLElement ? document.activeElement : null
      if (!openModalCount) originalBodyOverflow = document.body.style.overflow
      element.showModal()
      openModalCount++
      hasScrollLock = true
      document.body.style.overflow = 'hidden'
      element.querySelector<HTMLElement>('[data-modal-autofocus]')?.focus()
    } else if (!open && element.open) {
      element.close()
      restore()
    }
  },
  { flush: 'post' }
)

onBeforeUnmount(() => {
  dialog.value?.close()
  restore()
})
</script>

<template>
  <Teleport to="body">
    <dialog
      v-bind="$attrs"
      ref="dialog"
      class="base-modal"
      :aria-labelledby="labelledby"
      aria-modal="true"
      @cancel.prevent="emit('close')"
      @close="onClose"
      @pointerdown="pointerStartedOnBackdrop = $event.target === dialog"
      @click="pointerStartedOnBackdrop && $event.target === dialog && emit('close')"
    >
      <div class="base-modal__body">
        <button
          class="base-modal__close"
          type="button"
          aria-label="Закрыть окно"
          @click="emit('close')"
        >
          <X :size="18" aria-hidden="true" />
        </button>
        <slot />
      </div>
    </dialog>
  </Teleport>
</template>

<style scoped>
.base-modal {
  max-width: calc(100vw - 48px);
  max-height: calc(100svh - 48px);
  padding: 0;
  border: 0;
  border-radius: var(--modal-radius, var(--border-radius-md));
  background: var(--modal-background, var(--color-background));
  box-shadow: inset 0 0 0 2px var(--modal-border-color, transparent);
  color: var(--color-text-primary);
  overflow: auto;
}
.base-modal::backdrop {
  background: var(--color-backdrop);
  backdrop-filter: blur(6px);
}
.base-modal__body {
  display: flex;
  flex-direction: column;
  position: relative;
}
.base-modal__close {
  position: absolute;
  top: 8px;
  right: 8px;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  padding: 0;
  border: 0;
  border-radius: var(--border-radius-sm);
  background: transparent;
  color: var(--color-text-secondary);
}
.base-modal__close:hover {
  color: var(--color-yellow);
}

@media (max-width: 768px) {
  .base-modal {
    max-width: calc(100vw - 16px);
    max-height: calc(100svh - 16px);
  }
  .base-modal__close {
    width: 44px;
    height: 44px;
    top: 4px;
    right: 4px;
    display: grid;
    place-items: center;
  }
}
</style>
