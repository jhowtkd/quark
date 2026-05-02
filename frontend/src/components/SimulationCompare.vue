<template>
  <div class="simulation-compare">
    <!-- Loading State -->
    <div v-if="loading" class="skeleton-compare-panel">
      <div class="skeleton-compare-column">
        <div v-for="n in 6" :key="n" class="skeleton-compare-card"></div>
      </div>
      <div class="skeleton-compare-divider"></div>
      <div class="skeleton-compare-column">
        <div v-for="n in 6" :key="n" class="skeleton-compare-card"></div>
      </div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="compare-error">
      <p>{{ $t('step5.compare.errorLoading') }}</p>
      <button class="retry-btn" @click="retry">
        {{ $t('step5.compare.retry') }}
      </button>
    </div>

    <!-- Empty History -->
    <div v-else-if="history.length === 0" class="compare-empty">
      <p>{{ $t('step5.compare.noHistory') }}</p>
    </div>

    <!-- Main Content -->
    <template v-else>
      <!-- Selectors -->
      <div class="compare-selectors">
        <div class="selector-column">
          <label class="selector-label">{{ $t('step5.compare.selectBase') }}</label>
          <select v-model="lhsId" class="sim-select lhs-select">
            <option
              v-for="sim in sortedHistory"
              :key="sim.simulation_id"
              :value="sim.simulation_id"
            >
              {{ sim.project_name || $t('history.untitledSimulation') }} — {{ formatDate(sim.created_at) }}
            </option>
          </select>
          <div v-if="lhsSim" class="sim-mini-card">
            <span class="sim-name">{{ lhsSim.project_name || $t('history.untitledSimulation') }}</span>
            <span class="sim-date">{{ formatDate(lhsSim.created_at) }}</span>
            <span class="sim-badge" :class="lhsSim.status">{{ lhsSim.status }}</span>
            <span class="sim-rounds">{{ lhsSim.total_rounds || 0 }} rounds</span>
          </div>
        </div>

        <button class="swap-btn" :title="$t('step5.compare.swap')" @click="swapSides">
          <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="17 1 21 5 17 9"></polyline>
            <path d="M3 11V9a4 4 0 0 1 4-4h14"></path>
            <polyline points="7 23 3 19 7 15"></polyline>
            <path d="M21 13v2a4 4 0 0 1-4 4H3"></path>
          </svg>
        </button>

        <div class="selector-column">
          <label class="selector-label">{{ $t('step5.compare.selectTarget') }}</label>
          <select v-model="rhsId" class="sim-select rhs-select">
            <option value="">{{ $t('step5.compare.selectTarget') }}</option>
            <option
              v-for="sim in rhsHistoryOptions"
              :key="sim.simulation_id"
              :value="sim.simulation_id"
            >
              {{ sim.project_name || $t('history.untitledSimulation') }} — {{ formatDate(sim.created_at) }}
            </option>
          </select>
          <div v-if="rhsSim" class="sim-mini-card">
            <span class="sim-name">{{ rhsSim.project_name || $t('history.untitledSimulation') }}</span>
            <span class="sim-date">{{ formatDate(rhsSim.created_at) }}</span>
            <span class="sim-badge" :class="rhsSim.status">{{ rhsSim.status }}</span>
            <span class="sim-rounds">{{ rhsSim.total_rounds || 0 }} rounds</span>
          </div>
          <div v-else class="sim-placeholder">
            {{ $t('step5.compare.selectToCompare') }}
          </div>
        </div>
      </div>

      <!-- Metrics -->
      <div class="compare-section">
        <h3 class="section-title">{{ $t('step5.compare.metricsTitle') }}</h3>
        <div class="compare-metrics">
          <div class="metrics-column">
            <div
              v-for="(metric, idx) in lhsMetrics"
              :key="`lhs-${idx}`"
              class="metric-card"
            >
              <div class="metric-value">{{ metric.value }}</div>
              <div class="metric-label">{{ metric.label }}</div>
            </div>
          </div>

          <div class="metrics-delta">
            <div
              v-for="(delta, idx) in metricDeltas"
              :key="`delta-${idx}`"
              class="delta-row"
              :class="{ positive: delta.positive, negative: delta.negative, equal: delta.equal }"
            >
              <span v-if="delta.equal">=</span>
              <span v-else-if="delta.positive">↑ {{ delta.abs }}</span>
              <span v-else>↓ {{ delta.abs }}</span>
            </div>
          </div>

          <div class="metrics-column">
            <div
              v-for="(metric, idx) in rhsMetrics"
              :key="`rhs-${idx}`"
              class="metric-card"
              :class="{ placeholder: !rhsData }"
            >
              <div class="metric-value">{{ rhsData ? metric.value : '—' }}</div>
              <div class="metric-label">{{ metric.label }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Timeline -->
      <div class="compare-section">
        <div class="section-header-row">
          <h3 class="section-title">{{ $t('step5.compare.timelineTitle') }}</h3>
          <button class="toggle-expand-btn" @click="timelineExpanded = !timelineExpanded">
            {{ timelineExpanded ? $t('step5.compare.collapseAll') : $t('step5.compare.expandAll') }}
          </button>
        </div>
        <div class="compare-timeline">
          <div class="timeline-legend">
            <span class="legend-item lhs-legend">{{ $t('step5.compare.selectBase') }}</span>
            <span class="legend-item rhs-legend">{{ $t('step5.compare.selectTarget') }}</span>
          </div>
          <div class="timeline-chart">
            <div
              v-for="round in displayedTimelineRounds"
              :key="round.round_num"
              class="timeline-round"
            >
              <span class="round-label">{{ round.round_num }}</span>
              <div class="round-bars">
                <div
                  v-if="round.lhsCount !== null"
                  class="timeline-bar-lhs"
                  :style="{ height: round.lhsPct + '%' }"
                  :title="`${$t('step5.compare.selectBase')}: ${round.lhsCount} ações`"
                ></div>
                <div
                  v-if="round.rhsCount !== null"
                  class="timeline-bar-rhs"
                  :style="{ height: round.rhsPct + '%' }"
                  :title="`${$t('step5.compare.selectTarget')}: ${round.rhsCount} ações`"
                ></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Agents -->
      <div class="compare-section">
        <h3 class="section-title">{{ $t('step5.compare.agentsTitle') }}</h3>
        <div class="compare-agents">
          <!-- LHS Top Agents -->
          <div class="agents-column">
            <h4 class="agents-subtitle">{{ $t('step5.compare.selectBase') }}</h4>
            <table class="agents-table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>{{ $t('step5.dashboard.topAgents') }}</th>
                  <th>{{ $t('step5.compare.actions') }}</th>
                  <th>TW</th>
                  <th>RD</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(agent, idx) in lhsTopAgents" :key="agent.agent_id || idx">
                  <td>{{ idx + 1 }}</td>
                  <td>{{ agent.agent_name }}</td>
                  <td>{{ agent.total_actions }}</td>
                  <td>{{ agent.twitter_actions }}</td>
                  <td>{{ agent.reddit_actions }}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- RHS Top Agents -->
          <div class="agents-column">
            <h4 class="agents-subtitle">{{ $t('step5.compare.selectTarget') }}</h4>
            <table class="agents-table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>{{ $t('step5.dashboard.topAgents') }}</th>
                  <th>{{ $t('step5.compare.actions') }}</th>
                  <th>TW</th>
                  <th>RD</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(agent, idx) in rhsTopAgents" :key="agent.agent_id || idx">
                  <td>{{ idx + 1 }}</td>
                  <td>{{ agent.agent_name }}</td>
                  <td>{{ agent.total_actions }}</td>
                  <td>{{ agent.twitter_actions }}</td>
                  <td>{{ agent.reddit_actions }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Common Agents -->
        <div v-if="commonAgents.length > 0" class="common-agents">
          <h4 class="agents-subtitle">{{ $t('step5.compare.commonAgents') }}</h4>
          <table class="agents-table">
            <thead>
              <tr>
                <th>{{ $t('step5.dashboard.topAgents') }}</th>
                <th>{{ $t('step5.compare.selectBase') }}</th>
                <th>{{ $t('step5.compare.selectTarget') }}</th>
                <th>Delta</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="agent in commonAgents.slice(0, 5)" :key="agent.agent_name">
                <td>{{ agent.agent_name }}</td>
                <td>{{ agent.lhsActions }}</td>
                <td>{{ agent.rhsActions }}</td>
                <td :class="{ positive: agent.deltaPct > 0, negative: agent.deltaPct < 0 }">
                  {{ agent.deltaPct > 0 ? '+' : '' }}{{ agent.deltaPct }}%
                </td>
              </tr>
            </tbody>
          </table>
          <button
            v-if="commonAgents.length > 5"
            class="view-more-btn"
            @click="showAllCommon = !showAllCommon"
          >
            {{ showAllCommon ? $t('step5.compare.collapseAll') : $t('step5.compare.expandAll') }}
          </button>
        </div>

        <!-- Unique Agents -->
        <div class="unique-agents">
          <div v-if="uniqueLhsAgents.length > 0" class="unique-column">
            <h4 class="agents-subtitle">{{ $t('step5.compare.uniqueAgentsLhs') }}</h4>
            <ul class="unique-list">
              <li v-for="agent in uniqueLhsAgents.slice(0, 5)" :key="agent.agent_name">
                {{ agent.agent_name }} ({{ agent.total_actions }})
              </li>
            </ul>
          </div>
          <div v-if="uniqueRhsAgents.length > 0" class="unique-column">
            <h4 class="agents-subtitle">{{ $t('step5.compare.uniqueAgentsRhs') }}</h4>
            <ul class="unique-list">
              <li v-for="agent in uniqueRhsAgents.slice(0, 5)" :key="agent.agent_name">
                {{ agent.agent_name }} ({{ agent.total_actions }})
              </li>
            </ul>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { getSimulationHistory, getSimulation, getAgentStats, getSimulationTimeline } from '../api/simulation'

const { t } = useI18n()

const props = defineProps({
  baseSimulationId: { type: String, required: true }
})

// State
const history = ref([])
const lhsId = ref(props.baseSimulationId)
const rhsId = ref('')
const lhsData = ref(null)
const rhsData = ref(null)
const loading = ref(false)
const error = ref(null)
const timelineExpanded = ref(false)
const showAllCommon = ref(false)

// Computed
const sortedHistory = computed(() => {
  return [...history.value].sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
})

const rhsHistoryOptions = computed(() => {
  return sortedHistory.value.filter(sim => sim.simulation_id !== lhsId.value)
})

const lhsSim = computed(() => {
  return sortedHistory.value.find(s => s.simulation_id === lhsId.value) || null
})

const rhsSim = computed(() => {
  return sortedHistory.value.find(s => s.simulation_id === rhsId.value) || null
})

const lhsMetrics = computed(() => {
  if (!lhsData.value) return []
  const meta = lhsData.value.meta || {}
  const stats = lhsData.value.stats || []
  const totalActions = meta.total_actions_count || stats.reduce((s, a) => s + (a.total_actions || 0), 0)
  return [
    { label: t('step5.compare.agents'), value: meta.profiles_count || stats.length || 0 },
    { label: t('step5.compare.rounds'), value: meta.total_rounds || meta.current_round || 0 },
    { label: t('step5.compare.actions'), value: totalActions },
    { label: t('step5.compare.twitterActions'), value: meta.twitter_actions_count || 0 },
    { label: t('step5.compare.redditActions'), value: meta.reddit_actions_count || 0 },
    { label: t('step5.compare.simulatedHours'), value: meta.simulated_hours || 0 }
  ]
})

const rhsMetrics = computed(() => {
  if (!rhsData.value) return []
  const meta = rhsData.value.meta || {}
  const stats = rhsData.value.stats || []
  const totalActions = meta.total_actions_count || stats.reduce((s, a) => s + (a.total_actions || 0), 0)
  return [
    { label: t('step5.compare.agents'), value: meta.profiles_count || stats.length || 0 },
    { label: t('step5.compare.rounds'), value: meta.total_rounds || meta.current_round || 0 },
    { label: t('step5.compare.actions'), value: totalActions },
    { label: t('step5.compare.twitterActions'), value: meta.twitter_actions_count || 0 },
    { label: t('step5.compare.redditActions'), value: meta.reddit_actions_count || 0 },
    { label: t('step5.compare.simulatedHours'), value: meta.simulated_hours || 0 }
  ]
})

const metricDeltas = computed(() => {
  if (!rhsData.value || !lhsData.value) {
    return Array(6).fill({ equal: true, positive: false, negative: false, abs: 0 })
  }
  const lhs = lhsMetrics.value
  const rhs = rhsMetrics.value
  return lhs.map((lm, i) => {
    const rv = rhs[i]?.value || 0
    const lv = lm.value || 0
    const diff = rv - lv
    return {
      equal: diff === 0,
      positive: diff > 0,
      negative: diff < 0,
      abs: Math.abs(diff)
    }
  })
})

const maxTimelineRound = computed(() => {
  const lhsRounds = lhsData.value?.timeline?.length || 0
  const rhsRounds = rhsData.value?.timeline?.length || 0
  return Math.max(lhsRounds, rhsRounds)
})

const displayedTimelineRounds = computed(() => {
  const limit = timelineExpanded.value ? Infinity : 100
  const maxRound = maxTimelineRound.value
  const rounds = []
  const lhsTimeline = lhsData.value?.timeline || []
  const rhsTimeline = rhsData.value?.timeline || []

  let maxCount = 1
  for (let i = 0; i < Math.min(maxRound, limit); i++) {
    const lhsItem = lhsTimeline[i]
    const rhsItem = rhsTimeline[i]
    const lhsCount = lhsItem ? (lhsItem.twitter_actions || 0) + (lhsItem.reddit_actions || 0) : null
    const rhsCount = rhsItem ? (rhsItem.twitter_actions || 0) + (rhsItem.reddit_actions || 0) : null
    maxCount = Math.max(maxCount, lhsCount || 0, rhsCount || 0)
  }

  for (let i = 0; i < Math.min(maxRound, limit); i++) {
    const lhsItem = lhsTimeline[i]
    const rhsItem = rhsTimeline[i]
    const lhsCount = lhsItem ? (lhsItem.twitter_actions || 0) + (lhsItem.reddit_actions || 0) : null
    const rhsCount = rhsItem ? (rhsItem.twitter_actions || 0) + (rhsItem.reddit_actions || 0) : null
    rounds.push({
      round_num: i + 1,
      lhsCount,
      rhsCount,
      lhsPct: lhsCount !== null ? (lhsCount / maxCount) * 100 : 0,
      rhsPct: rhsCount !== null ? (rhsCount / maxCount) * 100 : 0
    })
  }
  return rounds
})

const lhsTopAgents = computed(() => {
  if (!lhsData.value) return []
  const stats = lhsData.value.stats || []
  return [...stats].sort((a, b) => (b.total_actions || 0) - (a.total_actions || 0)).slice(0, 5)
})

const rhsTopAgents = computed(() => {
  if (!rhsData.value) return []
  const stats = rhsData.value.stats || []
  return [...stats].sort((a, b) => (b.total_actions || 0) - (a.total_actions || 0)).slice(0, 5)
})

const commonAgents = computed(() => {
  if (!lhsData.value || !rhsData.value) return []
  const lhsStats = lhsData.value.stats || []
  const rhsStats = rhsData.value.stats || []
  const rhsMap = new Map(rhsStats.map(a => [a.agent_name, a]))
  const common = []
  for (const lhsAgent of lhsStats) {
    const rhsAgent = rhsMap.get(lhsAgent.agent_name)
    if (rhsAgent) {
      const lhsActions = lhsAgent.total_actions || 0
      const rhsActions = rhsAgent.total_actions || 0
      const deltaPct = lhsActions > 0 ? (((rhsActions - lhsActions) / lhsActions) * 100).toFixed(1) : '0.0'
      common.push({
        agent_name: lhsAgent.agent_name,
        lhsActions,
        rhsActions,
        deltaPct: parseFloat(deltaPct)
      })
    }
  }
  return common.sort((a, b) => Math.abs(b.deltaPct) - Math.abs(a.deltaPct))
})

const uniqueLhsAgents = computed(() => {
  if (!lhsData.value || !rhsData.value) return []
  const rhsNames = new Set((rhsData.value.stats || []).map(a => a.agent_name))
  return (lhsData.value.stats || []).filter(a => !rhsNames.has(a.agent_name))
    .sort((a, b) => (b.total_actions || 0) - (a.total_actions || 0))
})

const uniqueRhsAgents = computed(() => {
  if (!lhsData.value || !rhsData.value) return []
  const lhsNames = new Set((lhsData.value.stats || []).map(a => a.agent_name))
  return (rhsData.value.stats || []).filter(a => !lhsNames.has(a.agent_name))
    .sort((a, b) => (b.total_actions || 0) - (a.total_actions || 0))
})

// Methods
const loadHistory = async () => {
  try {
    const res = await getSimulationHistory(50)
    if (res.success && res.data) {
      const list = Array.isArray(res.data) ? res.data : (res.data.history || [])
      history.value = list.filter(s => s.status === 'completed')
    } else {
      history.value = []
    }
  } catch (err) {
    error.value = err.message || t('step5.compare.errorLoading')
  }
}

const loadComparisonData = async (simulationId, target) => {
  if (!simulationId) return
  loading.value = true
  error.value = null
  try {
    const [simRes, statsRes, timelineRes] = await Promise.all([
      getSimulation(simulationId),
      getAgentStats(simulationId),
      getSimulationTimeline(simulationId, 0, null)
    ])

    const meta = simRes.success && simRes.data ? simRes.data : {}
    const statsData = statsRes.success && statsRes.data ? statsRes.data : {}
    const stats = Array.isArray(statsData) ? statsData : (statsData.stats || [])
    const timelineData = timelineRes.success && timelineRes.data ? timelineRes.data : {}
    const timeline = Array.isArray(timelineData) ? timelineData : (timelineData.timeline || [])

    const data = { meta, stats, timeline }
    if (target === 'lhs') {
      lhsData.value = data
    } else {
      rhsData.value = data
    }
  } catch (err) {
    error.value = err.message || t('step5.compare.errorLoading')
  } finally {
    loading.value = false
  }
}

const retry = () => {
  error.value = null
  loadHistory()
  if (lhsId.value) loadComparisonData(lhsId.value, 'lhs')
  if (rhsId.value) loadComparisonData(rhsId.value, 'rhs')
}

const swapSides = () => {
  const temp = lhsId.value
  lhsId.value = rhsId.value || lhsId.value
  rhsId.value = temp === lhsId.value ? '' : temp
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  try {
    return new Date(dateStr).toLocaleDateString('pt-BR')
  } catch {
    return dateStr
  }
}

// Watchers
watch(lhsId, (newId) => {
  if (newId) loadComparisonData(newId, 'lhs')
})

watch(rhsId, (newId) => {
  if (newId) {
    loadComparisonData(newId, 'rhs')
  } else {
    rhsData.value = null
  }
})

// Lifecycle
onMounted(() => {
  loadHistory()
  if (lhsId.value) {
    loadComparisonData(lhsId.value, 'lhs')
  }
})
</script>

<style scoped>
.simulation-compare {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  padding: 20px;
  gap: 24px;
}

/* Skeleton */
.skeleton-compare-panel {
  display: flex;
  gap: 20px;
}

.skeleton-compare-column {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.skeleton-compare-divider {
  width: 40px;
}

.skeleton-compare-card {
  height: 80px;
  background: var(--color-surface-container-low);
  border-radius: 4px;
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* Error */
.compare-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 40px;
  color: var(--color-error);
}

.retry-btn {
  padding: 8px 16px;
  font-size: 13px;
  font-weight: 500;
  color: var(--color-surface);
  background: var(--color-on-background);
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

/* Empty */
.compare-empty {
  padding: 60px 20px;
  text-align: center;
  color: var(--color-muted);
  font-size: 14px;
}

/* Selectors */
.compare-selectors {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  background: var(--color-surface-container-low);
  border-radius: 4px;
  border: 1px solid var(--color-outline);
}

.selector-column {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.selector-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--color-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.sim-select {
  padding: 8px 10px;
  font-size: 13px;
  border: 1px solid var(--color-outline);
  border-radius: 6px;
  background: var(--color-surface);
  color: var(--color-on-surface);
  cursor: pointer;
  width: 100%;
}

.sim-select:focus {
  outline: none;
  border-color: var(--color-on-background);
}

.swap-btn {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-surface);
  border: 1px solid var(--color-outline);
  border-radius: 6px;
  cursor: pointer;
  color: var(--color-muted);
  transition: all 0.2s ease;
  margin-top: 20px;
  flex-shrink: 0;
}

.swap-btn:hover {
  border-color: var(--color-on-background);
  color: var(--color-on-background);
}

.sim-mini-card {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  background: var(--color-surface);
  border: 1px solid var(--color-outline);
  border-radius: 6px;
  font-size: 12px;
}

.sim-name {
  font-weight: 600;
  color: var(--color-on-background);
}

.sim-date {
  color: var(--color-muted);
}

.sim-badge {
  padding: 2px 8px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  border-radius: 4px;
}

.sim-badge.completed {
  background: #D1FAE5;
  color: #047857;
}

.sim-rounds {
  margin-left: auto;
  color: var(--color-muted);
  font-family: 'JetBrains Mono', monospace;
}

.sim-placeholder {
  padding: 24px;
  text-align: center;
  color: var(--color-muted);
  font-size: 13px;
  background: var(--color-surface);
  border: 1px dashed var(--color-outline);
  border-radius: 6px;
}

/* Sections */
.compare-section {
  background: var(--color-surface-container-low);
  border-radius: 4px;
  padding: 20px;
  border: 1px solid var(--color-outline);
}

.section-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-on-background);
  margin: 0 0 16px 0;
}

.section-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.toggle-expand-btn {
  padding: 6px 12px;
  font-size: 12px;
  font-weight: 500;
  color: var(--color-muted);
  background: var(--color-surface);
  border: 1px solid var(--color-outline);
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.toggle-expand-btn:hover {
  color: var(--color-on-surface);
  border-color: var(--color-on-background);
}

/* Metrics */
.compare-metrics {
  display: grid;
  grid-template-columns: 1fr 60px 1fr;
  gap: 12px;
  align-items: start;
}

.metrics-column {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.metric-card {
  background: var(--color-surface);
  padding: 14px 16px;
  border-radius: 4px;
  border: 1px solid var(--color-outline);
  transition: all 0.2s ease;
}

.metric-card.placeholder {
  opacity: 0.6;
}

.metric-value {
  font-size: 24px;
  font-weight: 700;
  color: var(--color-on-background);
  line-height: 1.2;
  margin-bottom: 4px;
}

.metric-label {
  font-size: 11px;
  font-weight: 500;
  color: var(--color-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.metrics-delta {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding-top: 14px;
}

.delta-row {
  height: 58px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-muted);
}

.delta-row.positive {
  color: #047857;
}

.delta-row.negative {
  color: #DC2626;
}

/* Timeline */
.compare-timeline {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.timeline-legend {
  display: flex;
  gap: 16px;
  font-size: 12px;
  font-weight: 500;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.legend-item::before {
  content: '';
  width: 12px;
  height: 12px;
  border-radius: 2px;
}

.lhs-legend::before {
  background: var(--color-primary);
}

.rhs-legend::before {
  background: #F97316;
}

.timeline-chart {
  display: flex;
  align-items: flex-end;
  gap: 4px;
  height: 160px;
  overflow-x: auto;
  padding-bottom: 4px;
}

.timeline-round {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  min-width: 20px;
  flex: 1;
}

.round-label {
  font-size: 10px;
  color: var(--color-muted);
}

.round-bars {
  display: flex;
  align-items: flex-end;
  gap: 2px;
  height: 120px;
  width: 100%;
  justify-content: center;
}

.timeline-bar-lhs {
  width: 8px;
  background: var(--color-primary);
  border-radius: 2px 2px 0 0;
  min-height: 2px;
  transition: height 0.3s ease;
}

.timeline-bar-rhs {
  width: 8px;
  background: #F97316;
  border-radius: 2px 2px 0 0;
  min-height: 2px;
  transition: height 0.3s ease;
}

/* Agents */
.compare-agents {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.agents-column {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.agents-subtitle {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin: 0;
}

.agents-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.agents-table thead th {
  padding: 8px 6px;
  text-align: left;
  font-size: 11px;
  font-weight: 600;
  color: var(--color-muted);
  text-transform: uppercase;
  letter-spacing: 0.03em;
  border-bottom: 1px solid var(--color-outline);
}

.agents-table tbody td {
  padding: 8px 6px;
  border-bottom: 1px solid var(--color-outline);
  color: var(--color-on-surface);
}

.common-agents {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid var(--color-outline);
}

.common-agents .positive {
  color: #047857;
  font-weight: 600;
}

.common-agents .negative {
  color: #DC2626;
  font-weight: 600;
}

.unique-agents {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid var(--color-outline);
}

.unique-list {
  list-style: none;
  padding: 0;
  margin: 0;
  font-size: 13px;
  color: var(--color-on-surface);
}

.unique-list li {
  padding: 6px 0;
  border-bottom: 1px solid var(--color-outline);
}

.view-more-btn {
  margin-top: 10px;
  padding: 6px 12px;
  font-size: 12px;
  font-weight: 500;
  color: var(--color-muted);
  background: var(--color-surface);
  border: 1px solid var(--color-outline);
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.view-more-btn:hover {
  color: var(--color-on-surface);
  border-color: var(--color-on-background);
}

@media (max-width: 768px) {
  .compare-selectors {
    flex-direction: column;
  }

  .swap-btn {
    margin-top: 0;
    align-self: center;
  }

  .compare-metrics {
    grid-template-columns: 1fr 40px 1fr;
  }

  .compare-agents {
    grid-template-columns: 1fr;
  }

  .unique-agents {
    grid-template-columns: 1fr;
  }
}
</style>
