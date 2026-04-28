<template>
  <div class="skeleton-table">
    <div class="skeleton-header">
      <SkeletonBlock v-for="c in columns" :key="`h-${c}`" width="80%" height="14px" />
    </div>
    <div v-for="r in rows" :key="`r-${r}`" class="skeleton-row">
      <SkeletonBlock v-for="c in columns" :key="`r${r}-${c}`" width="70%" height="12px" />
    </div>
  </div>
</template>

<script setup>
import SkeletonBlock from './SkeletonBlock.vue'

defineProps({
  rows: { type: Number, default: 5 },
  columns: { type: Number, default: 3 },
})
</script>

<style scoped>
.skeleton-table {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  border: 1px solid var(--color-outline);
  padding: var(--space-4);
}

.skeleton-header,
.skeleton-row {
  display: grid;
  grid-template-columns: repeat(v-bind(columns), 1fr);
  gap: var(--space-4);
  align-items: center;
}

.skeleton-header {
  padding-bottom: var(--space-2);
  border-bottom: 1px solid var(--color-outline);
}
</style>
