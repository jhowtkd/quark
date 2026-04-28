<template>
  <svg :width="width" :height="height" class="mini-sparkline">
    <polyline
      :points="points"
      fill="none"
      :stroke="color"
      stroke-width="2"
      stroke-linecap="round"
      stroke-linejoin="round"
    />
    <circle
      v-for="(p, i) in pointCoords"
      :key="i"
      :cx="p.x"
      :cy="p.y"
      :r="3"
      :fill="color"
    />
  </svg>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  data: { type: Array, required: true },
  width: { type: Number, default: 120 },
  height: { type: Number, default: 40 },
  color: { type: String, default: 'var(--color-primary)' },
})

const max = computed(() => Math.max(...props.data, 1))
const min = computed(() => Math.min(...props.data, 0))

const pointCoords = computed(() => {
  const range = max.value - min.value || 1
  return props.data.map((val, i) => ({
    x: (i / (props.data.length - 1 || 1)) * props.width,
    y: props.height - ((val - min.value) / range) * props.height,
  }))
})

const points = computed(() => {
  return pointCoords.value.map(p => `${p.x},${p.y}`).join(' ')
})
</script>

<style scoped>
.mini-sparkline {
  display: block;
}
</style>
