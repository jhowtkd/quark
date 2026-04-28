<template>
  <div class="skeleton-text">
    <SkeletonBlock
      v-for="i in lines"
      :key="i"
      :width="i === lines && lastLineWidth ? lastLineWidth : '100%'"
      height="12px"
    />
  </div>
</template>

<script setup>
import SkeletonBlock from './SkeletonBlock.vue'

const props = defineProps({
  lines: { type: Number, default: 3 },
  lastLineWidth: { type: String, default: '60%' },
})
</script>

<style scoped>
.skeleton-text {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}
</style>
