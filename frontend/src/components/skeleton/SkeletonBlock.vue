<template>
  <div class="skeleton-block" :style="blockStyle" />
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  width: { type: String, default: '100%' },
  height: { type: String, default: '16px' },
  rounded: { type: Boolean, default: false },
})

const blockStyle = computed(() => ({
  width: props.width,
  height: props.height,
  borderRadius: props.rounded ? '999px' : 'var(--radius-md)',
}))
</script>

<style scoped>
.skeleton-block {
  background: linear-gradient(
    90deg,
    var(--color-surface-container-low) 25%,
    var(--color-surface) 50%,
    var(--color-surface-container-low) 75%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}

@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}
</style>
