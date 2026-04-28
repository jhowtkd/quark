<template>
  <span :class="badgeClasses">
    <slot />
  </span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  variant: {
    type: String,
    default: 'default',
    validator: (v) => ['default', 'success', 'warning', 'error', 'info', 'accent'].includes(v),
  },
  size: {
    type: String,
    default: 'md',
    validator: (v) => ['sm', 'md'].includes(v),
  },
})

const badgeClasses = computed(() => {
  return ['base-badge', `variant-${props.variant}`, `size-${props.size}`]
})
</script>

<style scoped>
.base-badge {
  display: inline-flex;
  align-items: center;
  font-family: var(--font-machine);
  font-weight: var(--font-weight-medium);
  border-radius: var(--radius-md);
  line-height: var(--line-height-tight);
  white-space: nowrap;
}

/* Sizes */
.size-sm { padding: 2px 8px; font-size: var(--text-xs); }
.size-md { padding: 4px 10px; font-size: var(--text-sm); }

/* Variants */
.variant-default {
  background: var(--color-surface-container-highest);
  color: var(--color-muted);
}

.variant-success {
  background: var(--color-success-bg);
  color: var(--color-success);
}

.variant-warning {
  background: var(--color-warning-bg);
  color: var(--color-warning);
}

.variant-error {
  background: var(--color-error-bg);
  color: var(--color-error);
}

.variant-info {
  background: var(--color-info-bg);
  color: var(--color-info);
}

.variant-accent {
  background: var(--profile-primary);
  color: var(--color-on-primary);
}
</style>
