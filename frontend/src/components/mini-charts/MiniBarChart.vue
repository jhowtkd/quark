<template>
  <div class="mini-bar-chart">
    <div
      v-for="item in data"
      :key="item.label"
      class="bar-row"
    >
      <span class="bar-label">{{ item.label }}</span>
      <div class="bar-track">
        <div
          class="bar-fill"
          :style="{ width: `${(item.value / maxValue) * 100}%`, background: color }"
        />
      </div>
      <span class="bar-value">{{ item.value }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  data: { type: Array, required: true },
  color: { type: String, default: 'var(--color-primary)' },
})

const maxValue = computed(() => {
  return Math.max(...props.data.map(d => d.value), 1)
})
</script>

<style scoped>
.mini-bar-chart {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  font-size: var(--text-sm);
}

.bar-row {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.bar-label {
  min-width: 80px;
  font-family: var(--font-machine);
  color: var(--color-muted);
}

.bar-track {
  flex: 1;
  height: 8px;
  background: var(--color-surface-container-low);
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  transition: width 0.6s ease;
}

.bar-value {
  min-width: 40px;
  text-align: right;
  font-family: var(--font-machine);
  font-weight: var(--font-weight-medium);
  color: var(--color-on-background);
}
</style>
