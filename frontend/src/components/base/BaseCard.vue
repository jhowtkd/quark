<template>
  <div :class="cardClasses">
    <slot />
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  variant: {
    type: String,
    default: 'default',
    validator: (v) => ['default', 'elevated', 'outlined'].includes(v),
  },
  padding: {
    type: String,
    default: 'md',
    validator: (v) => ['sm', 'md', 'lg'].includes(v),
  },
  brutalist: { type: Boolean, default: false },
})

const cardClasses = computed(() => {
  const classes = ['base-card', `variant-${props.variant}`, `padding-${props.padding}`]
  if (props.brutalist) classes.push('brutalist')
  return classes
})
</script>

<style scoped>
.base-card {
  background: var(--color-surface);
  border-radius: var(--radius-md);
  transition: all 0.15s ease;
}

/* Variants */
.variant-default {
  border: 1px solid var(--color-outline);
}

.variant-elevated {
  border: none;
  box-shadow: var(--shadow-soft);
}

.variant-outlined {
  background: transparent;
  border: 1px solid var(--color-outline);
}

/* Padding */
.padding-sm { padding: var(--space-3); }
.padding-md { padding: var(--space-4); }
.padding-lg { padding: var(--space-6); }

/* Brutalist */
.brutalist {
  border: 2px solid var(--color-on-background);
  box-shadow: var(--shadow-brutalist);
}
.brutalist:hover {
  transform: translate(-2px, -2px);
}
</style>
