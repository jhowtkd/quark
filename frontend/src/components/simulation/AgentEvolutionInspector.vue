<template>
  <div class="agent-evolution-inspector" v-if="hasData">
    <div class="inspector-section">
      <h3>{{ $t('evolution.mostInfluenced') }}</h3>
      <ul class="agent-list">
        <li v-for="agent in mostInfluenced" :key="agent.agent_id">
          {{ agent.agent_name }} — {{ $t('evolution.influence') }}: {{ formatMetric(agent.social_influence) }}
        </li>
      </ul>
    </div>

    <div class="inspector-section">
      <h3>{{ $t('evolution.mostInfluential') }}</h3>
      <ul class="agent-list">
        <li v-for="agent in mostInfluential" :key="agent.agent_id">
          {{ agent.agent_name }} — {{ $t('evolution.influence') }}: {{ formatMetric(agent.social_influence) }}
        </li>
      </ul>
    </div>

    <div class="inspector-section">
      <h3>{{ $t('evolution.mostPolarized') }}</h3>
      <ul class="agent-list">
        <li v-for="agent in mostPolarized" :key="agent.agent_id">
          {{ agent.agent_name }} — {{ $t('evolution.polarization') }}: {{ formatMetric(agent.polarization_risk) }}
        </li>
      </ul>
    </div>

    <div class="inspector-section">
      <h3>{{ $t('evolution.metricTimeline') }}</h3>
      <div v-for="agent in timelineAgents" :key="agent.agent_id" class="timeline-agent">
        <strong>{{ agent.agent_name }}</strong>
        <div class="timeline-metrics">
          <div v-for="(value, metric) in agent.metrics" :key="metric" class="timeline-metric">
            <span class="metric-name">{{ $t(`evolution.metrics.${metric}`) }}</span>
            <span class="metric-value">{{ formatMetric(value) }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
  <div v-else class="evolution-empty" role="status">
    {{ $t('evolution.noEvidence') }}
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
  return props.evolution?.snapshots && Object.keys(props.evolution.snapshots).length > 0
})

const snapshotsList = computed(() => {
  return Object.values(props.evolution?.snapshots || {})
})

const mostInfluenced = computed(() => {
  return [...snapshotsList.value]
    .sort((a, b) => (b.social_influence || 0) - (a.social_influence || 0))
    .slice(0, 5)
})

const mostInfluential = computed(() => {
  return [...snapshotsList.value]
    .sort((a, b) => (b.social_influence || 0) - (a.social_influence || 0))
    .slice(0, 5)
})

const mostPolarized = computed(() => {
  return [...snapshotsList.value]
    .sort((a, b) => (b.polarization_risk || 0) - (a.polarization_risk || 0))
    .slice(0, 5)
})

const timelineAgents = computed(() => {
  return snapshotsList.value.map((snap) => ({
    agent_id: snap.agent_id,
    agent_name: snap.agent_name,
    metrics: {
      social_influence: snap.social_influence,
      polarization_risk: snap.polarization_risk,
      fatigue: snap.fatigue,
      evidence_openness: snap.evidence_openness,
      narrative_alignment: snap.narrative_alignment,
      trust_level: snap.trust_level,
    },
  }))
})

function formatMetric(value) {
  if (value == null) return '-'
  return typeof value === 'number' ? value.toFixed(2) : value
}
</script>

<style scoped>
.agent-evolution-inspector {
  padding: 16px;
}

.inspector-section {
  margin-bottom: 20px;
}

.inspector-section h3 {
  font-size: 0.9rem;
  margin: 0 0 8px;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.agent-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.agent-list li {
  padding: 4px 0;
  font-size: 0.85rem;
}

.timeline-agent {
  margin-bottom: 12px;
  padding: 8px;
  background: var(--bg-secondary);
  border-radius: 4px;
}

.timeline-metrics {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 8px;
  margin-top: 6px;
}

.timeline-metric {
  display: flex;
  justify-content: space-between;
  font-size: 0.8rem;
}

.metric-name {
  color: var(--text-secondary);
}

.metric-value {
  font-weight: 600;
}

.evolution-empty {
  padding: 24px;
  text-align: center;
  color: var(--text-secondary);
  font-size: 0.9rem;
}
</style>
