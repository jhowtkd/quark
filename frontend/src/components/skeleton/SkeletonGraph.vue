<template>
  <div class="skeleton-graph">
    <svg viewBox="0 0 400 200" class="skeleton-svg">
      <!-- Edges -->
      <line v-for="(edge, i) in edges" :key="`e-${i}`"
        :x1="edge.x1" :y1="edge.y1"
        :x2="edge.x2" :y2="edge.y2"
        class="skeleton-edge"
      />
      <!-- Nodes -->
      <circle v-for="(node, i) in nodes" :key="`n-${i}`"
        :cx="node.x" :cy="node.y" :r="node.r"
        class="skeleton-node"
      />
    </svg>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  nodeCount: { type: Number, default: 8 },
})

const nodes = computed(() => {
  const result = []
  for (let i = 0; i < props.nodeCount; i++) {
    const angle = (i / props.nodeCount) * Math.PI * 2
    const cx = 200 + Math.cos(angle) * 80
    const cy = 100 + Math.sin(angle) * 60
    result.push({ x: cx, y: cy, r: 8 + Math.random() * 8 })
  }
  return result
})

const edges = computed(() => {
  const result = []
  const n = nodes.value
  for (let i = 0; i < n.length; i++) {
    for (let j = i + 1; j < n.length; j++) {
      const dx = n[i].x - n[j].x
      const dy = n[i].y - n[j].y
      const dist = Math.sqrt(dx * dx + dy * dy)
      if (dist < 120) {
        result.push({ x1: n[i].x, y1: n[i].y, x2: n[j].x, y2: n[j].y })
      }
    }
  }
  return result.slice(0, 12)
})
</script>

<style scoped>
.skeleton-graph {
  width: 100%;
  height: 200px;
  background: var(--color-surface-container-low);
  border: 1px solid var(--color-outline);
  display: flex;
  align-items: center;
  justify-content: center;
}

.skeleton-svg {
  width: 100%;
  height: 100%;
}

.skeleton-node {
  fill: var(--color-outline);
  opacity: 0.6;
  animation: pulse 1.5s infinite ease-in-out;
}

.skeleton-edge {
  stroke: var(--color-outline);
  stroke-width: 1.5;
  opacity: 0.4;
}

@keyframes pulse {
  0%, 100% { opacity: 0.4; }
  50% { opacity: 0.8; }
}
</style>
