<template>
  <button
    :class="buttonClasses"
    :disabled="disabled || loading"
    :type="type"
    @click="$emit('click', $event)"
  >
    <Icon v-if="loading" name="loader-2" :size="iconSize" class="spin" />
    <slot />
  </button>
</template>

<script setup>
import { computed } from 'vue'
import Icon from '../Icon.vue'

const props = defineProps({
  variant: {
    type: String,
    default: 'primary',
    validator: (v) => ['primary', 'secondary', 'outline', 'ghost', 'danger'].includes(v),
  },
  size: {
    type: String,
    default: 'md',
    validator: (v) => ['sm', 'md', 'lg'].includes(v),
  },
  disabled: { type: Boolean, default: false },
  loading: { type: Boolean, default: false },
  brutalist: { type: Boolean, default: false },
  type: { type: String, default: 'button' },
})

defineEmits(['click'])

const buttonClasses = computed(() => {
  const classes = ['base-button', `variant-${props.variant}`, `size-${props.size}`]
  if (props.brutalist) classes.push('brutalist')
  if (props.disabled) classes.push('disabled')
  return classes
})

const iconSize = computed(() => {
  const map = { sm: 14, md: 16, lg: 18 }
  return map[props.size] || 16
})
</script>

<style scoped>
.base-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  font-family: var(--font-machine);
  font-weight: var(--font-weight-medium);
  border: none;
  cursor: pointer;
  transition: all 0.15s cubic-bezier(0.4, 0, 0.2, 1);
  border-radius: var(--radius-md);
  line-height: var(--line-height-tight);
  will-change: transform, box-shadow;
}

/* Sizes */
.size-sm { padding: var(--space-1) var(--space-3); font-size: var(--text-sm); }
.size-md { padding: var(--space-2) var(--space-4); font-size: var(--text-base); }
.size-lg { padding: var(--space-3) var(--space-6); font-size: var(--text-lg); }

/* Variants */
.variant-primary {
  background: var(--color-primary);
  color: var(--color-on-primary);
}
.variant-primary:hover:not(:disabled) {
  background: var(--color-primary-hover);
  transform: translateY(-1px);
  box-shadow: var(--shadow-soft);
}
.variant-primary:active:not(:disabled) {
  background: var(--color-primary-active);
  transform: scale(0.98);
  box-shadow: none;
}

.variant-secondary {
  background: var(--color-surface-container-highest);
  color: var(--color-on-background);
}
.variant-secondary:hover:not(:disabled) {
  background: var(--color-outline);
  transform: translateY(-1px);
}
.variant-secondary:active:not(:disabled) {
  transform: scale(0.98);
}

.variant-outline {
  background: transparent;
  color: var(--color-on-background);
  border: 1px solid var(--color-outline);
}
.variant-outline:hover:not(:disabled) {
  background: var(--color-surface-container-low);
  border-color: var(--color-on-background);
}

.variant-ghost {
  background: transparent;
  color: var(--color-on-background);
}
.variant-ghost:hover:not(:disabled) {
  background: var(--color-surface-container-low);
}

.variant-danger {
  background: var(--color-error);
  color: var(--color-on-primary);
}
.variant-danger:hover:not(:disabled) {
  opacity: 0.85;
}

/* Brutalist */
.brutalist {
  box-shadow: var(--shadow-brutalist);
}
.brutalist:hover:not(:disabled) {
  transform: translate(-2px, -2px);
}
.brutalist:active:not(:disabled) {
  transform: translate(0, 0);
  box-shadow: none;
}

/* Disabled */
.base-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Loading spinner */
.spin {
  animation: spin 1s linear infinite;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
