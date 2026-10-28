<script setup lang="ts">
type ButtonVariant = 'yellow' | 'transparent'
type ButtonSize = 'small' | 'medium' | 'large'
type ButtonType = 'button' | 'submit' | 'reset'

interface Props {
  variant?: ButtonVariant
  size?: ButtonSize
  type?: ButtonType
  disabled?: boolean
  loading?: boolean
  fullWidth?: boolean
}

withDefaults(defineProps<Props>(), {
  variant: 'yellow',
  size: 'medium',
  type: 'button',
  disabled: false,
  loading: false,
  fullWidth: false,
})
</script>

<template>
  <button
    class="base-button"
    :class="[
      `base-button--${variant}`,
      `base-button--${size}`,
      { 'base-button--full-width': fullWidth },
    ]"
    :type="type"
    :disabled="disabled || loading"
    :aria-busy="loading"
  >
    <span v-if="loading" class="base-button__spinner" aria-hidden="true" />

    <span v-else-if="$slots['icon-left']" class="base-button__icon">
      <slot name="icon-left" />
    </span>

    <span class="base-button__label">
      <slot />
    </span>

    <span v-if="!loading && $slots['icon-right']" class="base-button__icon">
      <slot name="icon-right" />
    </span>
  </button>
</template>

<style scoped>
.base-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 12px;

  max-width: 100%;

  border: 1px solid transparent;
  border-radius: var(--border-radius-lg);

  font-family: var(--font-family-base);
  font-weight: var(--font-weight-semibold);
  line-height: 1.2;

  cursor: pointer;

  transition:
    background-color var(--transition-default),
    border-color var(--transition-default),
    color var(--transition-default),
    transform var(--transition-fast);
}

/* Variants */

.base-button--yellow {
  background-color: var(--color-yellow);
  color: var(--color-background);
}

.base-button--transparent {
  background-color: transparent;
  border-color: var(--color-border);
  color: var(--color-text-primary);
}

/* Sizes */

.base-button--small {
  min-height: 40px;
  padding: 10px 18px;
  font-size: 13px;
}

.base-button--medium {
  min-height: 46px;
  padding: 12px 24px;
  font-size: 14px;
}

.base-button--large {
  height: 81px;
  width: 365px;
  padding: 14px 30px;
  font-size: var(--font-size-text-2);
}

/* Width */

.base-button--full-width {
  width: 100%;
}

/* Hover */

@media (hover: hover) {
  .base-button--yellow:hover:not(:disabled) {
    background-color: color-mix(in srgb, var(--color-yellow) 85%, white);
  }

  .base-button--transparent:hover:not(:disabled) {
    background-color: color-mix(in srgb, var(--color-white) 10%, transparent);

    border-color: var(--color-text-primary);
  }
}

/* Active */

.base-button:active:not(:disabled) {
  transform: scale(0.98);
}

/* Disabled */

.base-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Content */

.base-button__label {
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.base-button__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.base-button__icon :deep(svg) {
  display: block;
  width: 20px;
  height: 20px;
}

/* Loading */

.base-button__spinner {
  width: 18px;
  height: 18px;
  flex-shrink: 0;

  border: 2px solid currentColor;
  border-right-color: transparent;
  border-radius: 50%;

  animation: button-spin 0.7s linear infinite;
}

@keyframes button-spin {
  to {
    transform: rotate(360deg);
  }
}

/* Reduced motion */

@media (prefers-reduced-motion: reduce) {
  .base-button {
    transition: none;
  }

  .base-button:active:not(:disabled) {
    transform: none;
  }

  .base-button__spinner {
    animation: none;
  }
}
</style>
