<template>
  <div class="agent-evolution-summary" v-if="hasData">
    <div class="evolution-metrics">
      <div class="metric-row">
        <span class="metric-label">{{ $t('evolution.fatigue') }}</span>
        <span class="metric-value">{{ formatMetric(averages.fatigue) }}</span>
      </div>
      <div class="metric-row">
        <span class="metric-label">{{ $t('evolution.polarization') }}</span>
        <span class="metric-value">{{ formatMetric(averages.polarization_risk) }}</span>
      </div>
      <div class="metric-row">
        <span class="metric-label">{{ $t('evolution.narrativeAlignment') }}</span>
        <span class="metric-value">{{ formatMetric(averages.narrative_alignment) }}</span>
      </div>
    </div>
    <div v-if="topChanged.length" class="top-changed">
      <h4>{{ $t('evolution.topChanged') }}</h4>
      <ul>
        <li v-for="agent in topChanged" :key="agent.agent_id">
          {{ agent.agent_name }} ({{ formatMetric(agent.change_score) }})
        </li>
      </ul>
    </div>
  </div>
  <div v-else class="evolution-empty" role="status">
    {{ $t('evolution.noData') }}
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  evolution: {
    type: Object,
    default: () => ({}),
  },
})

const hasData = computed(() => {
  return props.evolution?.summary?.averages != null
})

const averages = computed(() => {
  return props.evolution?.summary?.averages || {}
})

const topChanged = computed(() => {
  return props.evolution?.summary?.top_changed_agents || []
})

function formatMetric(value) {
  if (value == null) return '-'
  return typeof value === 'number' ? value.toFixed(2) : value
}
</script>

<style scoped>
.agent-evolution-summary {
  padding: 12px 0;
}

.evolution-metrics {
  display: flex;
  gap: 16px;
  margin-bottom: 12px;
}

.metric-row {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 80px;
}

.metric-label {
  font-size: 0.75rem;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.metric-value {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--text-primary);
}

.top-changed h4 {
  font-size: 0.8rem;
  margin: 0 0 6px;
  color: var(--text-secondary);
}

.top-changed ul {
  list-style: none;
  padding: 0;
  margin: 0;
  font-size: 0.85rem;
}

.top-changed li {
  padding: 2px 0;
}

.evolution-empty {
  padding: 12px;
  text-align: center;
  color: var(--text-secondary);
  font-size: 0.85rem;
}
</style>
